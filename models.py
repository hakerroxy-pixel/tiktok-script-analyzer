from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Video(db.Model):
    __tablename__ = "videos"
    id = db.Column(db.Integer, primary_key=True)
    tiktok_url = db.Column(db.Text, nullable=False)
    author = db.Column(db.Text)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    transcription = db.relationship("Transcription", backref="video", uselist=False, cascade="all,delete")
    analysis = db.relationship("Analysis", backref="video", uselist=False, cascade="all,delete")


class Transcription(db.Model):
    __tablename__ = "transcriptions"
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey("videos.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    duration_seconds = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Analysis(db.Model):
    __tablename__ = "analyses"
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey("videos.id"), nullable=False)
    hook_text = db.Column(db.Text)
    hook_type = db.Column(db.Text)
    hook_score = db.Column(db.Integer)
    structure = db.Column(db.Text)
    virality_score = db.Column(db.Integer)
    persuasion_elements = db.Column(db.Text)
    full_analysis_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    adaptations = db.relationship("Adaptation", backref="analysis", cascade="all,delete")


class Adaptation(db.Model):
    __tablename__ = "adaptations"
    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey("analyses.id"), nullable=False)
    product_or_topic = db.Column(db.Text, nullable=False)
    adapted_script = db.Column(db.Text, nullable=False)
    version_number = db.Column(db.Integer, default=1)
    hook_style = db.Column(db.Text)
    is_favorite = db.Column(db.Boolean, default=False)
    current_script = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    chat_messages = db.relationship("ChatMessage", backref="adaptation", cascade="all,delete")


class CrossAnalysis(db.Model):
    __tablename__ = "cross_analyses"
    id = db.Column(db.Integer, primary_key=True)
    video_ids = db.Column(db.Text, nullable=False)
    result_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"
    id = db.Column(db.Integer, primary_key=True)
    adaptation_id = db.Column(db.Integer, db.ForeignKey("adaptations.id"), nullable=False)
    role = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
