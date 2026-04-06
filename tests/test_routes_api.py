import json
from unittest.mock import patch


def test_api_transcribe_and_analyze(client):
    mock_transcription = {"text": "Hola esto es una prueba", "duration_seconds": 30.0}
    mock_analysis = {
        "hook": {"text": "Hola", "type": "saludo", "score": 5, "explanation": "Simple"},
        "structure": {"sections": [], "rhythm": "medio"},
        "virality_score": {"score": 5, "justification": "Ok", "positive_factors": [], "negative_factors": []},
        "persuasion_elements": [],
    }

    with patch("routes.api.transcribe_tiktok", return_value=mock_transcription), \
         patch("routes.api.analyze_script", return_value=mock_analysis):
        resp = client.post("/api/transcribe", json={"url": "https://www.tiktok.com/@user/video/123"})

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["transcription"]["text"] == "Hola esto es una prueba"
    assert data["analysis"]["virality_score"]["score"] == 5
    assert data["video_id"] is not None


def test_api_transcribe_missing_url(client):
    resp = client.post("/api/transcribe", json={})
    assert resp.status_code == 400


def test_api_adapt(client, db):
    from models import Video, Transcription, Analysis
    v = Video(tiktok_url="https://www.tiktok.com/@user/video/123")
    db.session.add(v)
    db.session.commit()
    t = Transcription(video_id=v.id, text="Original script", duration_seconds=30)
    a = Analysis(video_id=v.id, hook_text="test", virality_score=7,
                 full_analysis_json='{"hook": {"type": "pregunta"}}')
    db.session.add_all([t, a])
    db.session.commit()

    fake_versions = [
        {"version_number": 1, "hook_style": "pregunta", "script": "Guion adaptado para Creatina"},
    ]
    with patch("routes.api.generate_versions", return_value=fake_versions):
        resp = client.post(f"/api/adapt/{a.id}", json={"product_or_topic": "Creatina"})

    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["versions"]) == 1
    assert "Creatina" in data["versions"][0]["script"]
