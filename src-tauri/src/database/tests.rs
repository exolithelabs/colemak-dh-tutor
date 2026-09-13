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
fn rejects_legacy_development_databases_without_migration() {
    for version in [0, 1] {
        let dir = tempdir().unwrap();
        let legacy = Connection::open(dir.path().join("colemak.db")).unwrap();
        legacy.execute_batch("CREATE TABLE sentinel(value TEXT); INSERT INTO sentinel VALUES('untouched');").unwrap();
        legacy.pragma_update(None, "user_version", version).unwrap();
        assert!(Database::open(dir.path()).err().unwrap().contains("Unsupported development database"));
        assert_eq!(legacy.pragma_query_value(None, "user_version", |row| row.get::<_, i32>(0)).unwrap(), version);
        assert_eq!(legacy.query_row("SELECT value FROM sentinel", [], |row| row.get::<_, String>(0)).unwrap(), "untouched");
        assert!(!dir.path().join("colemak.pre-rust-v2.db").exists());
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
