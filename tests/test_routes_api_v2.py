import json
from unittest.mock import patch
from models import Video, Transcription, Analysis, Adaptation, ChatMessage


def _create_video_with_analysis(db):
    v = Video(tiktok_url="https://www.tiktok.com/@user/video/123")
    db.session.add(v)
    db.session.commit()
    t = Transcription(video_id=v.id, text="Original script text", duration_seconds=30)
    a = Analysis(
        video_id=v.id, hook_text="test hook", hook_type="pregunta",
        hook_score=8, virality_score=7,
        full_analysis_json='{"hook": {"type": "pregunta", "score": 8}, "virality_score": {"score": 7}, "persuasion_elements": []}',
    )
    db.session.add_all([t, a])
    db.session.commit()
    return v, t, a


def test_adapt_creates_5_versions(client, db):
    v, t, a = _create_video_with_analysis(db)
    fake_versions = [
        {"version_number": i + 1, "hook_style": s, "script": f"Script {i + 1}"}
        for i, s in enumerate(["pregunta", "dato_impactante", "controversia", "historia_personal", "promesa"])
    ]
    with patch("routes.api.generate_versions", return_value=fake_versions):
        resp = client.post(f"/api/adapt/{a.id}", json={"product_or_topic": "Creatina"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["versions"]) == 5
    assert data["versions"][0]["hook_style"] == "pregunta"


def test_favorite_adaptation(client, db):
    v, t, a = _create_video_with_analysis(db)
    ad = Adaptation(
        analysis_id=a.id, product_or_topic="Creatina",
        adapted_script="Script", current_script="Script",
        version_number=1, hook_style="pregunta",
    )
    db.session.add(ad)
    db.session.commit()
    resp = client.post(f"/api/adaptation/{ad.id}/favorite")
    assert resp.status_code == 200
    assert resp.get_json()["is_favorite"] is True


def test_chat_message(client, db):
    v, t, a = _create_video_with_analysis(db)
    ad = Adaptation(
        analysis_id=a.id, product_or_topic="Creatina",
        adapted_script="Script original", current_script="Script original",
        version_number=1, hook_style="pregunta",
    )
    db.session.add(ad)
    db.session.commit()
    with patch("routes.api.chat_refine", return_value="Script refinado"):
        resp = client.post(f"/api/chat/{ad.id}", json={"message": "Hazlo más corto"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["script"] == "Script refinado"
    assert data["message_id"] is not None


def test_cross_analyze(client, db):
    v1, t1, a1 = _create_video_with_analysis(db)
    # Need at least 2 videos
    v2 = Video(tiktok_url="https://www.tiktok.com/@user2/video/456")
    db.session.add(v2)
    db.session.commit()
    t2 = Transcription(video_id=v2.id, text="Second script", duration_seconds=25)
    a2 = Analysis(
        video_id=v2.id, hook_text="test2", hook_type="controversia",
        hook_score=9, virality_score=8,
        full_analysis_json='{"hook": {"type": "controversia", "score": 9}, "virality_score": {"score": 8}, "persuasion_elements": []}',
    )
    db.session.add_all([t2, a2])
    db.session.commit()

    fake_result = {"hook_patterns": {}, "winning_formula": "Use pregunta hooks"}
    with patch("routes.api.cross_analyze", return_value=fake_result):
        resp = client.post("/api/cross-analyze", json={"video_ids": [v1.id, v2.id]})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "winning_formula" in data["result"]
