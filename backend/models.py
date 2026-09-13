from .app import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    progress = db.relationship('Progress', backref='user', lazy=True)

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    level = db.Column(db.Integer, nullable=False) # 1 for home row, 2 for top, etc.

class Progress(db.Model):
    __table_args__ = (db.Index('ix_progress_user_id_id', 'user_id', 'id'),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    wpm = db.Column(db.Float)
    accuracy = db.Column(db.Float)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
