import tempfile
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


if __name__ == "__main__":
    unittest.main()
