from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from .app import db
from .models import Lesson, Progress, User


api = Blueprint("api", __name__, url_prefix="/api")

LESSONS = [
    ("Home Row - Basic", "arst neio", 1),
    ("Home Row - DH Focus", "astg neio m", 1),
    ("Home Row - Common Bigrams", "th he an in er re on at en nd st es", 1),
    ("Home Row - Short Words", "star rain note nest near sent east area sane", 1),
    ("Home Row - Fluency", "the rain in spain stays mainly in the plain", 1),
    ("Top Row - Left Hand", "qwfpg arst", 2),
    ("Top Row - Right Hand", "jluy; neio", 2),
    ("Top Row - Mixed", "quick flow glad play jump wolf quay", 2),
    ("Top Row - DH Precision", "page find peak grow just long your year", 2),
    ("Top Row - Sentences", "the quick brown fox jumps over the lazy dog", 2),
    ("Bottom Row - Basic", "zxc dv kh , . /", 3),
    ("Bottom Row - Words", "dock back view size zone kind half calm", 3),
    ("Bottom Row - Integration", "every day is a new chance to learn and grow", 3),
    ("Punctuation - Basic", "hello, world! how are you today? (fine.)", 3),
    ("Punctuation - Advanced", 'it\'s "great" to see you; let\'s start!', 3),
    ("Top 100 Words - Part 1", "the be of and a to in of it for not on with he as you do", 4),
    ("Top 100 Words - Part 2", "at this but his by from they we say her she or an will my", 4),
    ("Trigram Mastery", "the and ing her hat his tha ere for ent ion ter was", 4),
    ("Double Letters", "tell well keep book look feel seen soon moon summer", 4),
    ("Prose - Philosophy", "to be or not to be, that is the question of the soul.", 5),
    ("Prose - Technology", "artificial intelligence is the future of human computer interaction.", 5),
    ("Prose - Nature", "the mountains are calling and i must go to the peak.", 5),
    ("Numbers - Row 1", "12345 67890 54321 09876", 6),
    ("Coding - Python", 'import os, sys; print("path:", os.getcwd())', 6),
    ("Coding - CSS", "body { margin: 0; padding: 20px; display: flex; }", 6),
    ("Coding - HTML", '<div class="main"><h1>Hello World</h1></div>', 6),
    (
        "Mastery - Long Text",
        "four score and seven years ago our fathers brought forth on this continent a new nation "
        "conceived in liberty and dedicated to the proposition that all men are created equal.",
        7,
    ),
    ("Mastery - Colemak DH Stress", "bright green plants grow high above the dark deep valley below.", 7),
]


def seed_lessons() -> None:
    db.session.add_all(Lesson(title=title, content=content, level=level) for title, content, level in LESSONS)
    db.session.commit()


def json_object() -> dict | None:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


@api.get("/health")
def health():
    return jsonify({"status": "ok"})


@api.get("/lessons")
def get_lessons():
    lessons = db.session.execute(db.select(Lesson).order_by(Lesson.level, Lesson.id)).scalars()
    return jsonify(
        [{"id": lesson.id, "title": lesson.title, "content": lesson.content, "level": lesson.level} for lesson in lessons]
    )


@api.post("/user/progress")
def save_progress():
    data = json_object()
    if data is None:
        return jsonify({"error": "expected a JSON object"}), 400
    username = str(data.get("username", "")).strip()
    if not username or len(username) > 80:
        return jsonify({"error": "username must contain 1-80 characters"}), 400
    try:
        lesson_id = int(data["lesson_id"])
        wpm = float(data["wpm"])
        accuracy = float(data["accuracy"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "lesson_id, wpm, and accuracy must be numbers"}), 400
    if not (0 <= wpm <= 1000 and 0 <= accuracy <= 100):
        return jsonify({"error": "progress values are outside the accepted range"}), 400
    if db.session.get(Lesson, lesson_id) is None:
        return jsonify({"error": "unknown lesson"}), 404

    user = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()
    if user is None:
        user = User(username=username)
        db.session.add(user)
        try:
            db.session.flush()
        except IntegrityError:
            db.session.rollback()
            user = db.session.execute(db.select(User).filter_by(username=username)).scalar_one()

    db.session.add(Progress(user_id=user.id, lesson_id=lesson_id, wpm=wpm, accuracy=accuracy))
    db.session.commit()
    return jsonify({"status": "success"}), 201


@api.get("/user/progress/<username>")
def get_progress(username: str):
    user = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()
    if user is None:
        return jsonify([])
    progress = db.session.execute(
        db.select(Progress).filter_by(user_id=user.id).order_by(Progress.completed_at)
    ).scalars()
    return jsonify(
        [
            {
                "lesson_id": entry.lesson_id,
                "wpm": entry.wpm,
                "accuracy": entry.accuracy,
                "completed_at": entry.completed_at.isoformat(),
            }
            for entry in progress
        ]
    )
