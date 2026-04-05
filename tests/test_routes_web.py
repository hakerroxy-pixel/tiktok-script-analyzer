def test_index_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"TikTok Script Analyzer" in resp.data


def test_history_page(client):
    resp = client.get("/history")
    assert resp.status_code == 200
    assert b"Historial" in resp.data


def test_detail_page_with_video(client, db):
    from models import Video, Transcription, Analysis
    v = Video(tiktok_url="https://www.tiktok.com/@user/video/123", author="@user")
    db.session.add(v)
    db.session.commit()
    t = Transcription(video_id=v.id, text="Test transcript", duration_seconds=30)
    a = Analysis(video_id=v.id, hook_text="Test hook", hook_type="pregunta",
                 hook_score=8, virality_score=7,
                 structure='{"sections":[],"rhythm":"rápido"}',
                 persuasion_elements='[]',
                 full_analysis_json='{}')
    db.session.add_all([t, a])
    db.session.commit()
    resp = client.get(f"/history/{v.id}")
    assert resp.status_code == 200
    assert b"Test transcript" in resp.data


def test_detail_page_404(client):
    resp = client.get("/history/9999")
    assert resp.status_code == 404
