from models import Video, Transcription, Analysis, Adaptation


def _create_full_video(db):
    v = Video(tiktok_url="https://www.tiktok.com/@user/video/123", author="@user")
    db.session.add(v)
    db.session.commit()
    t = Transcription(video_id=v.id, text="Test transcript", duration_seconds=30)
    a = Analysis(
        video_id=v.id, hook_text="Test hook", hook_type="pregunta",
        hook_score=8, virality_score=7,
        structure='{"sections":[],"rhythm":"rápido"}',
        persuasion_elements='[]',
        full_analysis_json='{"hook":{"type":"pregunta","score":8},"virality_score":{"score":7},"persuasion_elements":[]}',
    )
    db.session.add_all([t, a])
    db.session.commit()
    return v, a


def test_cross_analysis_page(client):
    resp = client.get("/cross-analysis")
    assert resp.status_code == 200


def test_chat_page(client, db):
    v, a = _create_full_video(db)
    ad = Adaptation(
        analysis_id=a.id, product_or_topic="Creatina",
        adapted_script="Script", current_script="Script",
        version_number=1, hook_style="pregunta",
    )
    db.session.add(ad)
    db.session.commit()
    resp = client.get(f"/chat/{ad.id}")
    assert resp.status_code == 200
    assert b"Script" in resp.data


def test_chat_page_404(client):
    resp = client.get("/chat/9999")
    assert resp.status_code == 404
