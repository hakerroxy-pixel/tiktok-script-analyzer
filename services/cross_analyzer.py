import json
from openai import OpenAI

def build_cross_analysis_prompt(transcripts: list[str], analyses: list[dict]) -> str:
    videos_text = ""
    for i, (t, a) in enumerate(zip(transcripts, analyses), 1):
        hook_info = a.get("hook", {})
        virality = a.get("virality_score", {})
        persuasion = a.get("persuasion_elements", [])
        videos_text += f"\n--- VIDEO {i} ---\nTranscripción: {t}\nHook tipo: {hook_info.get('type', '?')}, score: {hook_info.get('score', '?')}\nViralidad: {virality.get('score', '?')}/10\nElementos persuasivos: {json.dumps(persuasion, ensure_ascii=False)}\n"

    return f"""Eres un experto en análisis de contenido viral con más de 10 años de experiencia en fitness y suplementos deportivos.

Analiza los siguientes {len(transcripts)} videos virales y encuentra los PATRONES GANADORES:

{videos_text}

Responde SOLO con un JSON válido (sin markdown, sin ```), con esta estructura:

{{
  "hook_patterns": {{
    "most_used": "tipo de hook más frecuente",
    "best_scoring": "tipo de hook con mejor score promedio",
    "types": [{{"type": "nombre", "count": 2, "avg_score": 7.5}}]
  }},
  "structure_patterns": {{
    "avg_hook_duration": "0-3s",
    "avg_total_duration": "45s",
    "common_rhythm": "rápido/medio/lento"
  }},
  "persuasion_patterns": [
    {{"technique": "nombre", "frequency": 3, "avg_effectiveness": "alta/media/baja"}}
  ],
  "common_themes": ["tema1", "tema2"],
  "winning_formula": "Un párrafo describiendo la fórmula ideal para un guion viral basado en estos patrones."
}}"""

def cross_analyze(transcripts: list[str], analyses: list[dict], client: OpenAI = None, api_key: str = None) -> dict:
    if client is None:
        client = OpenAI(api_key=api_key)
    prompt = build_cross_analysis_prompt(transcripts, analyses)
    response = client.chat.completions.create(model="gpt-4o", max_tokens=2000, messages=[{"role": "user", "content": prompt}])
    raw_text = response.choices[0].message.content.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
    return json.loads(raw_text)
