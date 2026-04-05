import json
from flask import Blueprint, render_template
from models import Video

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
