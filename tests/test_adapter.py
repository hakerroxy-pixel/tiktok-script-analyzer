import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.adapter import adapt_script, build_adaptation_prompt


def test_build_adaptation_prompt_contains_inputs():
    prompt = build_adaptation_prompt(
        original_transcript="Este es el guion original",
        analysis_summary="Hook: pregunta, Viralidad: 8/10",
        product_or_topic="Creatina Monohidrato"
    )
    assert "Este es el guion original" in prompt
    assert "Creatina Monohidrato" in prompt
    assert "Hook: pregunta, Viralidad: 8/10" in prompt


def test_adapt_script_returns_text():
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="Guion adaptado para Creatina...")]
    mock_client.messages.create.return_value = mock_message

    result = adapt_script(
        original_transcript="Guion original",
        analysis_summary="Hook: pregunta",
        product_or_topic="Creatina",
        client=mock_client,
    )

    assert "Creatina" in result
    mock_client.messages.create.assert_called_once()
