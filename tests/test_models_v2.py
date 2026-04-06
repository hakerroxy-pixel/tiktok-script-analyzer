from models import Video, Transcription, Analysis, Adaptation, CrossAnalysis, ChatMessage


def test_adaptation_new_fields(db):
    v = Video(tiktok_url="https://www.tiktok.com/@user/video/123")
    db.session.add(v)
    db.session.commit()
    a = Analysis(video_id=v.id, hook_text="test", virality_score=7)
    db.session.add(a)
    db.session.commit()
    ad = Adaptation(
        analysis_id=a.id,
        product_or_topic="Creatina",
        adapted_script="Script original",
        current_script="Script editado",
        version_number=1,
        hook_style="pregunta",
        is_favorite=False,
    )
    db.session.add(ad)
    db.session.commit()
    assert ad.version_number == 1
    assert ad.hook_style == "pregunta"
    assert ad.is_favorite is False
    assert ad.current_script == "Script editado"


def test_cross_analysis(db):
    ca = CrossAnalysis(
        video_ids='[1, 2, 3]',
        result_json='{"patterns": []}',
    )
    db.session.add(ca)
    db.session.commit()
    assert ca.id is not None
    assert ca.video_ids == '[1, 2, 3]'


def test_chat_messages(db):
    v = Video(tiktok_url="https://www.tiktok.com/@user/video/123")
    db.session.add(v)
    db.session.commit()
    a = Analysis(video_id=v.id, hook_text="test", virality_score=7)
    db.session.add(a)
    db.session.commit()
    ad = Adaptation(
        analysis_id=a.id, product_or_topic="Creatina",
        adapted_script="Script", current_script="Script",
        version_number=1, hook_style="pregunta",
    )
    db.session.add(ad)
    db.session.commit()

    msg1 = ChatMessage(adaptation_id=ad.id, role="user", content="Hazlo más corto")
    msg2 = ChatMessage(adaptation_id=ad.id, role="assistant", content="Script corto...")
    db.session.add_all([msg1, msg2])
    db.session.commit()

    assert len(ad.chat_messages) == 2
    assert ad.chat_messages[0].role == "user"
    assert ad.chat_messages[1].role == "assistant"
