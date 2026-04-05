import json
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.analyzer import analyze_script, build_analysis_prompt


def test_build_analysis_prompt_contains_transcript():
    prompt = build_analysis_prompt("Este es un guion de prueba")
    assert "Este es un guion de prueba" in prompt
    assert "hook" in prompt.lower()
    assert "viralidad" in prompt.lower()


def test_analyze_script_parses_json_response():
    fake_response = {
        "hook": {
            "text": "Sabías que la creatina...",
            "type": "pregunta",
            "score": 8,
            "explanation": "Genera curiosidad inmediata"
        },
        "structure": {
            "sections": [
                {"name": "Hook", "duration": "0-3s", "content": "Pregunta inicial"},
                {"name": "Desarrollo", "duration": "3-25s", "content": "Explicación"},
                {"name": "CTA", "duration": "25-30s", "content": "Link en bio"}
            ],
            "rhythm": "rápido"
        },
        "virality_score": {
            "score": 7,
            "justification": "Buen hook, tema popular",
            "positive_factors": ["Hook fuerte", "Tema trending"],
            "negative_factors": ["CTA débil"]
        },
        "persuasion_elements": [
            {"technique": "curiosidad", "usage": "Pregunta inicial", "effectiveness": "alta"},
            {"technique": "autoridad", "usage": "Datos científicos", "effectiveness": "media"}
        ]
    }

    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=json.dumps(fake_response, ensure_ascii=False))]
    mock_client.messages.create.return_value = mock_message

    result = analyze_script("Sabías que la creatina es el suplemento más estudiado...", client=mock_client)

    assert result["hook"]["score"] == 8
    assert result["hook"]["type"] == "pregunta"
    assert result["virality_score"]["score"] == 7
    assert len(result["persuasion_elements"]) == 2
