import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.chat import chat_refine, build_chat_prompt


def test_build_chat_prompt_contains_context():
    prompt = build_chat_prompt(
        original_transcript="Guion original",
        analysis_summary="Hook: pregunta, Viralidad: 8/10",
        current_script="Guion actual adaptado",
        chat_history=[
            {"role": "user", "content": "Hazlo más corto"},
            {"role": "assistant", "content": "Guion corto..."},
        ],
        user_message="Ahora agrega más urgencia",
    )
    assert "Guion original" in prompt[0]["content"]
    assert "Guion actual adaptado" in prompt[0]["content"]
    assert "Hazlo más corto" in str(prompt)
    assert "Ahora agrega más urgencia" in str(prompt)


def test_chat_refine_returns_script():
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Guion refinado con urgencia..."
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    result = chat_refine(
        original_transcript="Original",
        analysis_summary="Hook: pregunta",
        current_script="Actual",
        chat_history=[],
        user_message="Agrega urgencia",
        client=mock_client,
    )

    assert result == "Guion refinado con urgencia..."
