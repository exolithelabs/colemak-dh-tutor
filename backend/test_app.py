import tempfile
import sqlite3
import unittest
from pathlib import Path

from backend.app import create_app, db


class AppSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.token = "test-token"
        self.app = create_app(self.temp_dir.name, self.token)
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()
        self.temp_dir.cleanup()

    def test_requests_require_sidecar_token(self):
        response = self.client.get("/api/lessons")
        self.assertEqual(response.status_code, 401)

    def test_first_run_seeds_lessons(self):
        response = self.client.get("/api/lessons", headers={"X-App-Token": self.token})
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.get_json()), 20)

    def test_database_is_created_only_in_supplied_data_directory(self):
        database_path = Path(self.temp_dir.name) / "colemak.db"
        self.assertTrue(database_path.is_file())
        self.assertEqual(self.app.config["DATA_DIR"], str(Path(self.temp_dir.name).resolve()))

    def test_sqlite_safety_settings_are_enabled(self):
        with self.app.app_context():
            connection = db.engine.raw_connection()
            try:
                cursor = connection.cursor()
                self.assertEqual(cursor.execute("PRAGMA foreign_keys").fetchone()[0], 1)
                self.assertEqual(cursor.execute("PRAGMA journal_mode").fetchone()[0], "wal")
                self.assertEqual(cursor.execute("PRAGMA busy_timeout").fetchone()[0], 5000)
            finally:
                connection.close()

    def test_destructive_system_routes_do_not_exist(self):
        response = self.client.post("/api/system/stop", headers={"X-App-Token": self.token})
        self.assertEqual(response.status_code, 404)

    def post_progress(self, **changes):
        payload = {"username": "Test User", "lesson_id": 1, "wpm": 45, "accuracy": 98}
        payload.update(changes)
        return self.client.post("/api/user/progress", json=payload, headers={"X-App-Token": self.token})

    def test_rejects_invalid_progress_without_writes(self):
        for key, values in {
            "username": [None, True, {}, "", "x" * 81],
            "lesson_id": [True, 1.5, "1", 0, -1, 10**100],
            "wpm": [True, "12", None, -1, float("inf"), float("nan"), 10**400],
            "accuracy": [True, "98", None, -1, 101],
        }.items():
            for value in values:
                with self.subTest(key=key, value=value):
                    self.assertEqual(self.post_progress(**{key: value}).status_code, 400)
        response = self.client.get("/api/user/progress/Test%20User", headers={"X-App-Token": self.token})
        self.assertEqual(response.get_json(), [])

    def test_custom_progress_is_saved_but_not_listed_as_a_builtin_lesson(self):
        self.assertEqual(self.post_progress(lesson_id=999, accuracy=0).status_code, 201)
        headers = {"X-App-Token": self.token}
        entries = self.client.get("/api/user/progress/Test%20User", headers=headers).get_json()
        self.assertEqual(entries[0]["lesson_id"], 999)
        self.assertEqual(entries[0]["accuracy"], 0)
        self.assertTrue(entries[0]["completed_at"].endswith("Z"))
        lessons = self.client.get("/api/lessons", headers=headers).get_json()
        self.assertNotIn(999, [lesson["id"] for lesson in lessons])

    def test_history_is_paginated_newest_first_and_users_are_isolated(self):
        for wpm in (10, 20, 30):
            self.assertEqual(self.post_progress(wpm=wpm).status_code, 201)
        self.post_progress(username="Another user")
        headers = {"X-App-Token": self.token}
        first = self.client.get("/api/user/progress/Test%20User?limit=2", headers=headers).get_json()
        self.assertEqual([entry["wpm"] for entry in first], [30, 20])
        last = self.client.get(f'/api/user/progress/Test%20User?before={first[-1]["id"]}', headers=headers).get_json()
        self.assertEqual([entry["wpm"] for entry in last], [10])
        for query in ("limit=0", "limit=201", "limit=no", "before=-1"):
            self.assertEqual(self.client.get(f"/api/user/progress/Test%20User?{query}", headers=headers).status_code, 400)

    def test_untrusted_origin_and_host_are_rejected(self):
        headers = {"X-App-Token": self.token, "Origin": "https://evil.example"}
        self.assertEqual(self.client.get("/api/lessons", headers=headers).status_code, 403)
        self.assertEqual(self.client.options("/api/lessons", headers=headers).status_code, 403)
        headers = {"X-App-Token": self.token, "Host": "evil.example"}
        self.assertEqual(self.client.get("/api/lessons", headers=headers).status_code, 400)

    def test_preflight_security_headers_and_unicode_token(self):
        response = self.client.options("/api/lessons", headers={"Origin": "http://tauri.localhost"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Access-Control-Allow-Origin"], "http://tauri.localhost")
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertEqual(self.client.get("/api/lessons", headers={"X-App-Token": "é"}).status_code, 401)

    def test_malformed_and_oversize_bodies_are_rejected(self):
        headers = {"X-App-Token": self.token}
        for body in ("null", "[]", "{"):
            self.assertEqual(self.client.post("/api/user/progress", data=body, content_type="application/json", headers=headers).status_code, 400)
        response = self.client.post("/api/user/progress", data='"' + "x" * (1024 * 1024) + '"', content_type="application/json", headers=headers)
        self.assertEqual(response.status_code, 413)

    def test_reopening_database_preserves_progress(self):
        self.post_progress()
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()
        self.app = create_app(self.temp_dir.name, self.token)
        self.client = self.app.test_client()
        entries = self.client.get("/api/user/progress/Test%20User", headers={"X-App-Token": self.token}).get_json()
        self.assertEqual(len(entries), 1)

    def test_relative_data_directory_is_rejected(self):
        with self.assertRaises(ValueError):
            create_app("relative-data", self.token)

    def test_legacy_upgrade_creates_backup_and_preserves_progress(self):
        self.post_progress()
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()
        database_path = Path(self.temp_dir.name) / "colemak.db"
        with sqlite3.connect(database_path) as connection:
            connection.execute("PRAGMA user_version=0")
        connection.close()
        self.app = create_app(self.temp_dir.name, self.token)
        with sqlite3.connect(Path(self.temp_dir.name) / "colemak.pre-v1.db") as backup:
            self.assertEqual(backup.execute("SELECT count(*) FROM progress").fetchone()[0], 1)
            self.assertEqual(backup.execute("PRAGMA user_version").fetchone()[0], 0)
        backup.close()
        self.assertEqual(len(self.app.test_client().get("/api/user/progress/Test%20User", headers={"X-App-Token": self.token}).get_json()), 1)

    def test_newer_schema_is_not_opened_by_older_app(self):
        with tempfile.TemporaryDirectory() as directory:
            with sqlite3.connect(Path(directory) / "colemak.db") as connection:
                connection.execute("PRAGMA user_version=2")
            connection.close()
            with self.assertRaisesRegex(RuntimeError, "newer version"):
                create_app(directory, self.token)


if __name__ == "__main__":
    unittest.main()
