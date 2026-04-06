import json
import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.multi_adapter import generate_versions, build_multi_version_prompt

HOOK_STYLES = ["pregunta", "dato_impactante", "controversia", "historia_personal", "promesa"]


def test_build_prompt_contains_inputs():
    prompt = build_multi_version_prompt(
        original_transcript="Guion original aquí",
        analysis_summary="Hook: pregunta, Viralidad: 8/10",
        product_or_topic="Creatina",
    )
    assert "Guion original aquí" in prompt
    assert "Creatina" in prompt
    assert "pregunta" in prompt


def test_generate_versions_returns_5():
    fake_response = [
        {"version_number": i + 1, "hook_style": HOOK_STYLES[i], "script": f"Guion versión {i + 1}"}
        for i in range(5)
    ]
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = json.dumps(fake_response, ensure_ascii=False)
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    result = generate_versions(
        original_transcript="Guion original",
        analysis_summary="Hook: pregunta",
        product_or_topic="Creatina",
        client=mock_client,
    )

    assert len(result) == 5
    assert result[0]["version_number"] == 1
    assert result[0]["hook_style"] == "pregunta"
    assert "Guion versión 1" in result[0]["script"]
