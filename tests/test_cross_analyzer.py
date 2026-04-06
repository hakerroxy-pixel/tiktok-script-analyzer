import json
import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.cross_analyzer import cross_analyze, build_cross_analysis_prompt


def test_build_prompt_contains_analyses():
    analyses = [
        {"hook": {"type": "pregunta", "score": 8}, "virality_score": {"score": 7}},
        {"hook": {"type": "dato_impactante", "score": 9}, "virality_score": {"score": 8}},
    ]
    transcripts = ["Transcript 1", "Transcript 2"]
    prompt = build_cross_analysis_prompt(transcripts, analyses)
    assert "Transcript 1" in prompt
    assert "Transcript 2" in prompt
    assert "pregunta" in prompt


def test_cross_analyze_returns_patterns():
    fake_response = {
        "hook_patterns": {"most_used": "pregunta", "best_scoring": "dato_impactante", "types": [{"type": "pregunta", "count": 3, "avg_score": 7.5}]},
        "structure_patterns": {"avg_hook_duration": "0-3s", "avg_total_duration": "45s", "common_rhythm": "rápido"},
        "persuasion_patterns": [{"technique": "curiosidad", "frequency": 4, "avg_effectiveness": "alta"}],
        "common_themes": ["suplementos", "resultados"],
        "winning_formula": "Use pregunta hooks...",
    }
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = json.dumps(fake_response, ensure_ascii=False)
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    result = cross_analyze(transcripts=["T1", "T2"], analyses=[{"hook": {"type": "pregunta"}}], client=mock_client)
    assert "hook_patterns" in result
    assert "winning_formula" in result
