from models import Video, Transcription, Analysis, Adaptation


def test_create_video(db):
    v = Video(tiktok_url="https://www.tiktok.com/@user/video/123", author="@user")
    db.session.add(v)
    db.session.commit()
    assert v.id is not None
    assert v.tiktok_url == "https://www.tiktok.com/@user/video/123"


def test_video_with_transcription(db):
    v = Video(tiktok_url="https://www.tiktok.com/@user/video/123")
    db.session.add(v)
    db.session.commit()
    t = Transcription(video_id=v.id, text="Hello world", duration_seconds=30.0)
    db.session.add(t)
    db.session.commit()
    assert v.transcription.text == "Hello world"
    assert v.transcription.duration_seconds == 30.0


def test_video_with_analysis(db):
    v = Video(tiktok_url="https://www.tiktok.com/@user/video/123")
    db.session.add(v)
    db.session.commit()
    a = Analysis(
        video_id=v.id,
        hook_text="Did you know...",
        hook_type="pregunta",
        hook_score=8,
        virality_score=7,
        full_analysis_json='{"test": true}',
    )
    db.session.add(a)
    db.session.commit()
    assert v.analysis.hook_score == 8
    assert v.analysis.virality_score == 7


def test_analysis_with_adaptations(db):
    v = Video(tiktok_url="https://www.tiktok.com/@user/video/123")
    db.session.add(v)
    db.session.commit()
    a = Analysis(video_id=v.id, hook_text="test", virality_score=5)
    db.session.add(a)
    db.session.commit()
    ad1 = Adaptation(analysis_id=a.id, product_or_topic="Creatina", adapted_script="Script 1")
    ad2 = Adaptation(analysis_id=a.id, product_or_topic="Preentreno", adapted_script="Script 2")
    db.session.add_all([ad1, ad2])
    db.session.commit()
    assert len(a.adaptations) == 2
    assert a.adaptations[0].product_or_topic == "Creatina"
