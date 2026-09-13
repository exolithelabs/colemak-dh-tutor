import secrets
from pathlib import Path

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine


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
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


def create_app(data_dir: str | Path, auth_token: str | None = None) -> Flask:
    app = Flask(__name__)
    # The caller must choose an OS-managed per-user directory. Never default to
    # Flask's instance directory, which may be inside the source or install tree.
    storage_dir = Path(data_dir).expanduser().resolve()
    storage_dir.mkdir(parents=True, exist_ok=True)
    database_path = (storage_dir / "colemak.db").resolve()

    app.config.update(
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{database_path.as_posix()}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"connect_args": {"timeout": 5}},
        SIDECAR_AUTH_TOKEN=auth_token or secrets.token_urlsafe(32),
        DATA_DIR=str(storage_dir),
        MAX_CONTENT_LENGTH=1 * 1024 * 1024,
    )
    db.init_app(app)

    from .routes import api

    app.register_blueprint(api)

    @app.before_request
    def authenticate_request():
        if request.method == "OPTIONS":
            return None
        supplied_token = request.headers.get("X-App-Token", "")
        if not secrets.compare_digest(supplied_token, app.config["SIDECAR_AUTH_TOKEN"]):
            return jsonify({"error": "unauthorized"}), 401
        return None

    @app.after_request
    def apply_desktop_cors(response):
        origin = request.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-App-Token"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return response

    with app.app_context():
        from .models import Lesson
        from .routes import seed_lessons

        db.create_all()
        if not db.session.query(Lesson.id).first():
            seed_lessons()

    # On Unix-like systems this prevents other local users from reading newly
    # created progress data. Windows protects this folder through the user ACL.
    try:
        storage_dir.chmod(0o700)
        database_path.chmod(0o600)
    except OSError:
        app.logger.warning("Could not restrict permissions on the app data directory")

    return app
