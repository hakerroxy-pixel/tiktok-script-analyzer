import json
from flask import Blueprint, render_template
from models import Video, Adaptation, ChatMessage

web_bp = Blueprint("web", __name__)


@web_bp.route("/")
def index():
    return render_template("index.html")


@web_bp.route("/history")
def history():
    videos = Video.query.order_by(Video.created_at.desc()).limit(50).all()
    return render_template("history.html", videos=videos)


@web_bp.route("/history/<int:video_id>")
def detail(video_id):
    video = Video.query.get_or_404(video_id)
    analysis_data = None
    if video.analysis and video.analysis.full_analysis_json:
        try:
            analysis_data = json.loads(video.analysis.full_analysis_json)
        except json.JSONDecodeError:
            analysis_data = None
    return render_template("detail.html", video=video, analysis_data=analysis_data)


@web_bp.route("/profile/<username>")
def profile_page(username):
    return render_template("profile.html", username=username)


@web_bp.route("/cross-analysis")
def cross_analysis():
    videos = Video.query.order_by(Video.created_at.desc()).limit(50).all()
    return render_template("cross_analysis.html", videos=videos)


@web_bp.route("/chat/<int:adaptation_id>")
def chat_page(adaptation_id):
    adaptation = Adaptation.query.get_or_404(adaptation_id)
    messages = ChatMessage.query.filter_by(adaptation_id=adaptation_id)\
        .order_by(ChatMessage.created_at).all()
    return render_template("chat.html", adaptation=adaptation, messages=messages)
