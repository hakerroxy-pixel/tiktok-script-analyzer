import json
import re
from flask import Blueprint, request, jsonify, current_app, render_template
from models import db, Video, Transcription, Analysis, Adaptation, CrossAnalysis, ChatMessage
from services.transcriber import transcribe_tiktok
from services.analyzer import analyze_script
from services.multi_adapter import generate_versions
from services.cross_analyzer import cross_analyze
from services.chat import chat_refine
from services.tiktok_metrics import get_video_metrics, calculate_engagement
from services.tiktok_profile import get_profile_videos

api_bp = Blueprint("api", __name__)


@api_bp.route("/videos", methods=["GET"])
def api_videos():
    """List all analyzed videos (history)."""
    videos = Video.query.order_by(Video.created_at.desc()).limit(100).all()
    result = []
    for v in videos:
        item = {
            "id": v.id,
            "tiktok_url": v.tiktok_url,
            "author": v.author,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        if v.transcription:
            item["transcription"] = {"text": v.transcription.text, "duration_seconds": v.transcription.duration_seconds}
        if v.analysis:
            item["analysis"] = {
                "id": v.analysis.id,
                "hook_text": v.analysis.hook_text,
                "hook_type": v.analysis.hook_type,
                "hook_score": v.analysis.hook_score,
                "virality_score": v.analysis.virality_score,
            }
            try:
                item["analysis"]["full"] = json.loads(v.analysis.full_analysis_json)
            except (json.JSONDecodeError, TypeError):
                pass
            item["adaptations"] = [
                {
                    "id": ad.id,
                    "product_or_topic": ad.product_or_topic,
                    "version_number": ad.version_number,
                    "hook_style": ad.hook_style,
                    "script": ad.current_script or ad.adapted_script,
                    "is_favorite": ad.is_favorite,
                }
                for ad in v.analysis.adaptations
            ]
        result.append(item)
    return jsonify(result)


@api_bp.route("/video/<int:video_id>", methods=["GET"])
def api_video_detail(video_id):
    """Get full detail of a single video."""
    v = Video.query.get_or_404(video_id)
    item = {
        "id": v.id,
        "tiktok_url": v.tiktok_url,
        "author": v.author,
        "created_at": v.created_at.isoformat() if v.created_at else None,
    }
    if v.transcription:
        item["transcription"] = {"text": v.transcription.text, "duration_seconds": v.transcription.duration_seconds}
    if v.analysis:
        item["analysis"] = {
            "id": v.analysis.id,
            "hook_text": v.analysis.hook_text,
            "hook_type": v.analysis.hook_type,
            "hook_score": v.analysis.hook_score,
            "virality_score": v.analysis.virality_score,
        }
        try:
            item["analysis"]["full"] = json.loads(v.analysis.full_analysis_json)
        except (json.JSONDecodeError, TypeError):
            pass
        item["adaptations"] = [
            {
                "id": ad.id,
                "product_or_topic": ad.product_or_topic,
                "version_number": ad.version_number,
                "hook_style": ad.hook_style,
                "script": ad.current_script or ad.adapted_script,
                "is_favorite": ad.is_favorite,
            }
            for ad in v.analysis.adaptations
        ]
    return jsonify(item)


def extract_tiktok_author(url: str) -> str:
    match = re.search(r"tiktok\.com/@([^/]+)", url)
    return f"@{match.group(1)}" if match else None


@api_bp.route("/transcribe", methods=["POST"])
def api_transcribe():
    data = request.get_json() or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "URL is required"}), 400

    url = url.split("?")[0]

    try:
        result = transcribe_tiktok(
            tiktok_url=url,
            tmp_dir=current_app.config["TMP_DIR"],
            openai_api_key=current_app.config.get("OPENAI_API_KEY"),
            groq_api_key=current_app.config.get("GROQ_API_KEY"),
        )
    except Exception as e:
        return jsonify({"error": f"Error al transcribir: {str(e)}"}), 500

    try:
        analysis_data = analyze_script(
            transcript=result["text"],
            api_key=current_app.config.get("OPENAI_API_KEY"),
            groq_api_key=current_app.config.get("GROQ_API_KEY"),
        )
    except Exception as e:
        return jsonify({"error": f"Error al analizar: {str(e)}"}), 500

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

    try:
        versions = generate_versions(
            original_transcript=transcription.text,
            analysis_summary=analysis_summary,
            product_or_topic=product_or_topic,
            api_key=current_app.config.get("OPENAI_API_KEY"),
            groq_api_key=current_app.config.get("GROQ_API_KEY"),
        )
    except Exception as e:
        return jsonify({"error": f"Error al generar versiones: {str(e)}"}), 500

    saved_versions = []
    for v in versions:
        adaptation = Adaptation(
            analysis_id=analysis.id,
            product_or_topic=product_or_topic,
            adapted_script=v["script"],
            current_script=v["script"],
            version_number=v["version_number"],
            hook_style=v["hook_style"],
        )
        db.session.add(adaptation)
        db.session.flush()
        saved_versions.append({
            "adaptation_id": adaptation.id,
            "version_number": v["version_number"],
            "hook_style": v["hook_style"],
            "script": v["script"],
        })

    db.session.commit()

    return jsonify({
        "analysis_id": analysis.id,
        "product_or_topic": product_or_topic,
        "versions": saved_versions,
    })


@api_bp.route("/adaptation/<int:adaptation_id>/favorite", methods=["POST"])
def api_favorite(adaptation_id):
    adaptation = Adaptation.query.get_or_404(adaptation_id)
    adaptation.is_favorite = not adaptation.is_favorite
    db.session.commit()
    return jsonify({"adaptation_id": adaptation.id, "is_favorite": adaptation.is_favorite})


@api_bp.route("/chat/<int:adaptation_id>", methods=["POST"])
def api_chat(adaptation_id):
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "message is required"}), 400

    adaptation = Adaptation.query.get_or_404(adaptation_id)
    analysis = adaptation.analysis
    video = analysis.video
    transcription = video.transcription

    analysis_summary = f"Hook: {analysis.hook_type}, Score: {analysis.hook_score}/10, Viralidad: {analysis.virality_score}/10"

    chat_history = [
        {"role": m.role, "content": m.content}
        for m in ChatMessage.query.filter_by(adaptation_id=adaptation_id)
            .order_by(ChatMessage.created_at).all()
    ]

    try:
        refined = chat_refine(
            original_transcript=transcription.text,
            analysis_summary=analysis_summary,
            current_script=adaptation.current_script or adaptation.adapted_script,
            chat_history=chat_history,
            user_message=message,
            api_key=current_app.config["OPENAI_API_KEY"],
        )
    except Exception as e:
        return jsonify({"error": f"Error al refinar: {str(e)}"}), 500

    user_msg = ChatMessage(adaptation_id=adaptation_id, role="user", content=message)
    assistant_msg = ChatMessage(adaptation_id=adaptation_id, role="assistant", content=refined)
    db.session.add_all([user_msg, assistant_msg])

    adaptation.current_script = refined
    db.session.commit()

    return jsonify({
        "script": refined,
        "message_id": assistant_msg.id,
        "adaptation_id": adaptation_id,
    })


@api_bp.route("/metrics", methods=["POST"])
def api_metrics():
    """Get TikTok video metrics (views, likes, comments, shares) from URL."""
    data = request.get_json() or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        metrics = get_video_metrics(url)
        metrics["engagement_rate"] = calculate_engagement(metrics)
        return jsonify(metrics)
    except Exception as e:
        return jsonify({"error": f"Error getting metrics: {str(e)}"}), 500


@api_bp.route("/metrics/bulk", methods=["POST"])
def api_metrics_bulk():
    """Get metrics for multiple TikTok URLs."""
    data = request.get_json() or {}
    urls = data.get("urls", [])
    if not urls:
        return jsonify({"error": "urls array is required"}), 400

    results = []
    for url in urls:
        try:
            metrics = get_video_metrics(url.strip())
            metrics["engagement_rate"] = calculate_engagement(metrics)
            metrics["url"] = url.strip()
            results.append(metrics)
        except Exception as e:
            results.append({"url": url.strip(), "error": str(e)})

    return jsonify(results)


@api_bp.route("/profile", methods=["POST"])
def api_profile():
    """Get all videos from a TikTok profile with metrics."""
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    if not username:
        return jsonify({"error": "username is required"}), 400
    try:
        result = get_profile_videos(username)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500


@api_bp.route("/match-videos", methods=["POST"])
def api_match_videos():
    """Match TikTok videos with guiones by description similarity."""
    from difflib import SequenceMatcher

    data = request.get_json() or {}
    username = data.get("username", "").strip()
    guiones = data.get("guiones", [])

    if not username:
        return jsonify({"error": "username is required"}), 400
    if not guiones:
        return jsonify({"error": "guiones array is required"}), 400

    # 1. Get profile videos
    try:
        profile = get_profile_videos(username)
    except Exception as e:
        return jsonify({"error": f"Error fetching profile: {str(e)}"}), 500

    videos = profile.get("videos", [])[:10]  # Limit to last 10

    matches = []

    for vid in videos:
        desc = (vid.get("description") or "").strip().lower()
        best_match = None
        best_similarity = 0

        if desc and len(desc) > 10:
            # Match by description vs guion content
            for g in guiones:
                g_content = (g.get("content") or "").strip().lower()
                g_title = (g.get("title") or "").strip().lower()

                if not g_content:
                    continue

                # Compare first 50 chars
                sim1 = SequenceMatcher(None, desc[:50], g_content[:50]).ratio()

                # Also compare full description with guion words
                g_words = set(w for w in g_content.split() if len(w) > 4)
                d_words = set(desc.split())
                if g_words:
                    word_overlap = len(g_words & d_words) / len(g_words)
                else:
                    word_overlap = 0

                # Title match
                title_sim = SequenceMatcher(None, desc[:50], g_title[:50]).ratio() if g_title else 0

                similarity = max(sim1, word_overlap, title_sim)

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = g
        else:
            # Short/no description - try to transcribe
            vid_url = vid.get("url", "")
            if vid_url:
                try:
                    result = transcribe_tiktok(
                        tiktok_url=vid_url,
                        tmp_dir=current_app.config["TMP_DIR"],
                        groq_api_key=current_app.config.get("GROQ_API_KEY"),
                        openai_api_key=current_app.config.get("OPENAI_API_KEY"),
                    )
                    transcript = result.get("text", "").strip().lower()
                    if transcript:
                        for g in guiones:
                            g_content = (g.get("content") or "").strip().lower()
                            if not g_content:
                                continue
                            sim = SequenceMatcher(None, transcript[:50], g_content[:50]).ratio()
                            if sim > best_similarity:
                                best_similarity = sim
                                best_match = g
                except Exception as e:
                    print(f"Transcription failed for {vid_url}: {e}")

        if best_match and best_similarity > 0.3:
            matches.append({
                "video_id": vid.get("id", ""),
                "video_url": vid.get("url", ""),
                "video_description": vid.get("description", ""),
                "guion_id": best_match.get("id", ""),
                "guion_title": best_match.get("title", ""),
                "similarity": round(best_similarity, 2),
                "views": vid.get("views", 0),
                "likes": vid.get("likes", 0),
                "comments": vid.get("comments", 0),
                "shares": vid.get("shares", 0),
                "engagement_rate": vid.get("engagement_rate", 0),
                "cover": vid.get("cover", ""),
            })

    matches.sort(key=lambda x: x["similarity"], reverse=True)

    return jsonify({
        "username": username,
        "total_videos": len(videos),
        "matches": matches,
    })


@api_bp.route("/comments", methods=["POST"])
def api_comments():
    """Get comments from a TikTok video."""
    from services.tiktok_comments import get_video_comments
    data = request.get_json() or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "url is required"}), 400
    try:
        result = get_video_comments(url)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/followers", methods=["POST"])
def api_followers():
    """Get follower count for a TikTok user."""
    from services.tiktok_profile import get_follower_count
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    if not username:
        return jsonify({"error": "username is required"}), 400
    try:
        result = get_follower_count(username)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/cross-analyze", methods=["POST"])
def api_cross_analyze():
    data = request.get_json() or {}
    video_ids = data.get("video_ids", [])
    new_urls = data.get("new_urls", [])

    if not video_ids and not new_urls:
        return jsonify({"error": "Provide video_ids or new_urls"}), 400

    for url in new_urls:
        url = url.strip().split("?")[0]
        if not url:
            continue
        try:
            result = transcribe_tiktok(
                tiktok_url=url,
                tmp_dir=current_app.config["TMP_DIR"],
                openai_api_key=current_app.config["OPENAI_API_KEY"],
            )
            analysis_data = analyze_script(
                transcript=result["text"],
                api_key=current_app.config["OPENAI_API_KEY"],
            )
            video = Video(tiktok_url=url, author=extract_tiktok_author(url))
            db.session.add(video)
            db.session.commit()
            t = Transcription(video_id=video.id, text=result["text"], duration_seconds=result["duration_seconds"])
            a = Analysis(
                video_id=video.id,
                hook_text=analysis_data["hook"]["text"],
                hook_type=analysis_data["hook"]["type"],
                hook_score=analysis_data["hook"]["score"],
                structure=json.dumps(analysis_data["structure"], ensure_ascii=False),
                virality_score=analysis_data["virality_score"]["score"],
                persuasion_elements=json.dumps(analysis_data["persuasion_elements"], ensure_ascii=False),
                full_analysis_json=json.dumps(analysis_data, ensure_ascii=False),
            )
            db.session.add_all([t, a])
            db.session.commit()
            video_ids.append(video.id)
        except Exception as e:
            return jsonify({"error": f"Error procesando {url}: {str(e)}"}), 500

    transcripts = []
    analyses = []
    for vid in video_ids:
        video = Video.query.get(vid)
        if not video or not video.transcription or not video.analysis:
            continue
        transcripts.append(video.transcription.text)
        try:
            analyses.append(json.loads(video.analysis.full_analysis_json))
        except (json.JSONDecodeError, TypeError):
            continue

    if len(analyses) < 2:
        return jsonify({"error": "Se necesitan al menos 2 videos con análisis"}), 400

    try:
        result = cross_analyze(
            transcripts=transcripts,
            analyses=analyses,
            api_key=current_app.config["OPENAI_API_KEY"],
        )
    except Exception as e:
        return jsonify({"error": f"Error al analizar patrones: {str(e)}"}), 500

    ca = CrossAnalysis(
        video_ids=json.dumps(video_ids),
        result_json=json.dumps(result, ensure_ascii=False),
    )
    db.session.add(ca)
    db.session.commit()

    return jsonify({
        "cross_analysis_id": ca.id,
        "video_count": len(analyses),
        "result": result,
    })
