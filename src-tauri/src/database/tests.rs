use super::*;
use tempfile::tempdir;

fn input(lesson_id: i64, wpm: f64) -> ProgressInput {
    ProgressInput { username: "User1".into(), lesson_id, wpm, accuracy: 0.0 }
}

#[test]
fn fresh_database_and_restart_preserve_builtin_and_custom_results() {
    let dir = tempdir().unwrap();
    {
        let mut db = Database::open(dir.path()).unwrap();
        let lessons = db.lessons().unwrap();
        assert_eq!(lessons.len(), 28);
        assert_eq!(lessons[0].id, 1);
        assert_eq!(lessons[27].id, 28);
        db.save_progress(input(1, 42.0)).unwrap();
        db.save_progress(input(999, 50.0)).unwrap();
    }
    let db = Database::open(dir.path()).unwrap();
    let entries = db.progress("User1", 100, None).unwrap();
    assert_eq!(entries.len(), 2);
    assert_eq!(entries[0].lesson_id, 999);
    assert_eq!(entries[0].accuracy, 0.0);
    assert!(entries[0].completed_at.ends_with('Z'));
    assert!(!dir.path().join("colemak.pre-rust-v2.db").exists());
}

#[test]
fn migrates_both_python_schema_versions_with_a_consistent_backup() {
    for version in [0, 1] {
        let dir = tempdir().unwrap();
        // Same schema and timestamp representation emitted by Flask-SQLAlchemy.
        let legacy = Connection::open(dir.path().join("colemak.db")).unwrap();
        legacy.execute_batch("PRAGMA journal_mode=WAL;
            CREATE TABLE user(id INTEGER PRIMARY KEY, username VARCHAR(80) NOT NULL UNIQUE, created_at DATETIME);
            CREATE TABLE lesson(id INTEGER PRIMARY KEY, title VARCHAR(100) NOT NULL, content TEXT NOT NULL, level INTEGER NOT NULL);
            CREATE TABLE progress(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES user(id), lesson_id INTEGER NOT NULL REFERENCES lesson(id), wpm FLOAT, accuracy FLOAT, completed_at DATETIME);
            INSERT INTO user VALUES(7,'Existing user','2026-09-01 12:00:00.000000');
            INSERT INTO lesson VALUES(1,'Existing title','arst neio',1);
            INSERT INTO progress VALUES(42,7,1,55.5,97.2,'2026-09-01 12:01:00.123456');").unwrap();
        legacy.pragma_update(None, "user_version", version).unwrap();
        let mut db = Database::open(dir.path()).unwrap();
        let entry = &db.progress("Existing user", 100, None).unwrap()[0];
        assert_eq!(entry.id, 42);
        assert_eq!(entry.wpm, 55.5);
        assert_eq!(entry.completed_at, "2026-09-01T12:01:00.123456Z");
        assert_eq!(db.lessons().unwrap()[0].title, "Existing title");
        let backup = Connection::open(dir.path().join("colemak.pre-rust-v2.db")).unwrap();
        assert_eq!(backup.query_row("SELECT count(*) FROM progress", [], |row| row.get::<_, i64>(0)).unwrap(), 1);
        assert_eq!(backup.pragma_query_value(None, "user_version", |row| row.get::<_, i32>(0)).unwrap(), version);
        db.save_progress(input(999, 40.0)).unwrap();
        drop(db);
        let reopened = Database::open(dir.path()).unwrap();
        assert_eq!(reopened.progress("Existing user", 100, None).unwrap().len(), 1);
        assert_eq!(backup.query_row("SELECT count(*) FROM progress", [], |row| row.get::<_, i64>(0)).unwrap(), 1);
    }
}

#[test]
fn invalid_writes_roll_back_and_history_is_bounded_and_isolated() {
    let dir = tempdir().unwrap();
    let mut db = Database::open(dir.path()).unwrap();
    for value in [f64::NAN, f64::INFINITY, -1.0, 1001.0] {
        assert!(db.save_progress(input(1, value)).is_err());
    }
    for id in [-1, 0, 998, i64::MAX] { assert!(db.save_progress(input(id, 1.0)).is_err()); }
    let mut bad = input(1, 10.0);
    bad.username = " ".into();
    assert!(db.save_progress(bad).is_err());
    let mut bad = input(1, 10.0);
    bad.accuracy = 101.0;
    assert!(db.save_progress(bad).is_err());
    assert!(db.progress("User1", 100, None).unwrap().is_empty());
    for speed in [10.0, 20.0, 30.0] { db.save_progress(input(1, speed)).unwrap(); }
    let entries = db.progress("User1", 2, None).unwrap();
    assert_eq!(entries.iter().map(|entry| entry.wpm).collect::<Vec<_>>(), [30.0,20.0]);
    assert_eq!(db.progress("User1", 2, Some(entries[1].id)).unwrap()[0].wpm, 10.0);
    assert!(db.progress("someone else", 100, None).unwrap().is_empty());
    assert!(db.progress("User1", 201, None).is_err());
    assert!(db.progress("User1", 0, None).is_err());
    assert!(db.progress("User1", 100, Some(0)).is_err());
}

#[test]
fn rejects_newer_schema_and_relative_paths_without_modifying_data() {
    assert!(Database::open(Path::new("relative")).is_err());
    let dir = tempdir().unwrap();
    let connection = Connection::open(dir.path().join("colemak.db")).unwrap();
    connection.pragma_update(None, "user_version", 3).unwrap();
    assert!(Database::open(dir.path()).err().unwrap().contains("newer version"));
    assert_eq!(connection.pragma_query_value(None, "user_version", |row| row.get::<_, i32>(0)).unwrap(), 3);
    assert!(!dir.path().join("colemak.pre-rust-v2.db").exists());
}

#[test]
fn command_payload_rejects_wrong_types_and_unknown_fields() {
    for json in [
        r#"{"username":"User1","lesson_id":true,"wpm":1,"accuracy":100}"#,
        r#"{"username":"User1","lesson_id":1.5,"wpm":1,"accuracy":100}"#,
        r#"{"username":"User1","lesson_id":1,"wpm":"10","accuracy":100}"#,
        r#"{"username":"User1","lesson_id":1,"wpm":10,"accuracy":100,"sql":"DROP TABLE user"}"#,
    ] { assert!(serde_json::from_str::<ProgressInput>(json).is_err()); }
}
