import secrets
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine, URL
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException


db = SQLAlchemy()

ALLOWED_ORIGINS = {
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://tauri.localhost",
    "https://tauri.localhost",
    "tauri://localhost",
}


@event.listens_for(Engine, "connect")
def configure_sqlite(connection, _connection_record) -> None:
    """Use durable, contention-friendly settings for the local SQLite database."""
    if connection.__class__.__module__ != "sqlite3":
        return
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=FULL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


def create_app(data_dir: str | Path, auth_token: str | None = None) -> Flask:
    app = Flask(__name__)
    # The caller must choose an OS-managed per-user directory. Never default to
    # Flask's instance directory, which may be inside the source or install tree.
    if not data_dir or not Path(data_dir).expanduser().is_absolute():
        raise ValueError("data_dir must be an absolute per-user storage path")
    storage_dir = Path(data_dir).expanduser().resolve()
    storage_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    if os.name != "nt":
        storage_dir.chmod(0o700)
    database_path = (storage_dir / "colemak.db").resolve()
    if database_path.parent != storage_dir:
        raise ValueError("Database must not be a symlink outside the data directory")
    existed = database_path.exists()
    # Refuse unsafe downgrades and preserve legacy data before schema changes.
    with closing(sqlite3.connect(database_path)) as connection:
        schema_version = connection.execute("PRAGMA user_version").fetchone()[0]
        if schema_version > 1:
            raise RuntimeError("This database requires a newer version of Colemak-DH Tutor")
        if existed and schema_version == 0:
            backup_path = storage_dir / "colemak.pre-v1.db"
            if not backup_path.exists():
                with closing(sqlite3.connect(backup_path)) as backup:
                    connection.backup(backup)
                if os.name != "nt":
                    backup_path.chmod(0o600)
    if os.name != "nt":
        database_path.chmod(0o600)

    app.config.update(
        SQLALCHEMY_DATABASE_URI=URL.create("sqlite", database=database_path.as_posix()),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"connect_args": {"timeout": 5}},
        SIDECAR_AUTH_TOKEN=auth_token or secrets.token_urlsafe(32),
        DATA_DIR=str(storage_dir),
        MAX_CONTENT_LENGTH=1 * 1024 * 1024,
        TRUSTED_HOSTS=["127.0.0.1", "localhost"],
    )
    db.init_app(app)

    from .routes import api

    app.register_blueprint(api)

    @app.before_request
    def authenticate_request():
        origin = request.headers.get("Origin")
        if origin is not None and origin not in ALLOWED_ORIGINS:
            return jsonify({"error": "untrusted origin"}), 403
        if request.method == "OPTIONS":
            return None
        supplied_token = request.headers.get("X-App-Token", "")
        if not secrets.compare_digest(supplied_token.encode(), app.config["SIDECAR_AUTH_TOKEN"].encode()):
            return jsonify({"error": "unauthorized"}), 401
        return None

    @app.after_request
    def apply_desktop_cors(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        origin = request.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-App-Token"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return response

    @app.errorhandler(HTTPException)
    def http_error(error):
        response = error.get_response()
        response.data = app.json.dumps({"error": error.name})
        response.content_type = "application/json"
        return response

    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        db.session.rollback()
        app.logger.error("Database operation failed (%s)", type(error).__name__)
        return jsonify({"error": "Unable to access local progress. Check free disk space and restart the app."}), 503

    with app.app_context():
        from .models import Lesson, Progress
        from .routes import seed_lessons

        db.create_all()
        if not db.session.query(Lesson.id).filter(Lesson.id != 999).first():
            seed_lessons()
        # Reserve one stable lesson ID for custom practice; never store its text.
        if db.session.get(Lesson, 999) is None:
            db.session.add(Lesson(id=999, title="Custom Practice", content="", level=99))
            db.session.commit()
        # create_all does not add indexes to existing tables on upgrades.
        for index in Progress.__table__.indexes:
            index.create(bind=db.engine, checkfirst=True)
        with db.engine.begin() as connection:
            connection.exec_driver_sql("PRAGMA user_version=1")

    # On Unix-like systems this prevents other local users from reading newly
    # created progress data. Windows protects this folder through the user ACL.
    if os.name != "nt":
        database_path.chmod(0o600)

    return app
