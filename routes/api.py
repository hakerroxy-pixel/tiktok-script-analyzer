import json
import re
from flask import Blueprint, request, jsonify, current_app, render_template
from models import db, Video, Transcription, Analysis, Adaptation
from services.transcriber import transcribe_tiktok
from services.analyzer import analyze_script
from services.adapter import adapt_script

api_bp = Blueprint("api", __name__)


def extract_tiktok_author(url: str) -> str:
    match = re.search(r"tiktok\.com/@([^/]+)", url)
    return f"@{match.group(1)}" if match else None


@api_bp.route("/transcribe", methods=["POST"])
def api_transcribe():
    data = request.get_json() or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "URL is required"}), 400

    # Transcribe
    result = transcribe_tiktok(
        tiktok_url=url,
        tmp_dir=current_app.config["TMP_DIR"],
        openai_api_key=current_app.config["OPENAI_API_KEY"],
    )

    # Analyze
    analysis_data = analyze_script(
        transcript=result["text"],
        api_key=current_app.config["ANTHROPIC_API_KEY"],
    )

    # Save to DB
    video = Video(tiktok_url=url, author=extract_tiktok_author(url))
    db.session.add(video)
    db.session.commit()

    transcription = Transcription(
        video_id=video.id,
        text=result["text"],
        duration_seconds=result["duration_seconds"],
    )
    db.session.add(transcription)

    analysis = Analysis(
        video_id=video.id,
        hook_text=analysis_data["hook"]["text"],
        hook_type=analysis_data["hook"]["type"],
        hook_score=analysis_data["hook"]["score"],
        structure=json.dumps(analysis_data["structure"], ensure_ascii=False),
        virality_score=analysis_data["virality_score"]["score"],
        persuasion_elements=json.dumps(analysis_data["persuasion_elements"], ensure_ascii=False),
        full_analysis_json=json.dumps(analysis_data, ensure_ascii=False),
    )
    db.session.add(analysis)
    db.session.commit()

    return jsonify({
        "video_id": video.id,
        "transcription": {"text": result["text"], "duration_seconds": result["duration_seconds"]},
        "analysis": analysis_data,
    })


@api_bp.route("/adapt/<int:analysis_id>", methods=["POST"])
def api_adapt(analysis_id):
    data = request.get_json() or {}
    product_or_topic = data.get("product_or_topic", "").strip()
    if not product_or_topic:
        return jsonify({"error": "product_or_topic is required"}), 400

    analysis = Analysis.query.get_or_404(analysis_id)
    video = analysis.video
    transcription = video.transcription

    analysis_summary = f"Hook: {analysis.hook_type}, Score: {analysis.hook_score}/10, Viralidad: {analysis.virality_score}/10"

    adapted = adapt_script(
        original_transcript=transcription.text,
        analysis_summary=analysis_summary,
        product_or_topic=product_or_topic,
        api_key=current_app.config["ANTHROPIC_API_KEY"],
    )

    adaptation = Adaptation(
        analysis_id=analysis.id,
        product_or_topic=product_or_topic,
        adapted_script=adapted,
    )
    db.session.add(adaptation)
    db.session.commit()

    # If htmx request, return HTML partial
    if request.headers.get("HX-Request"):
        return render_template("partials/adaptation.html",
                               product_or_topic=product_or_topic,
                               adapted_script=adapted,
                               adaptation_id=adaptation.id)

    return jsonify({
        "adaptation_id": adaptation.id,
        "product_or_topic": product_or_topic,
        "adapted_script": adapted,
    })
