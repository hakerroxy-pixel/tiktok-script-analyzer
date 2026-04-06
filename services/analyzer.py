import json
from openai import OpenAI


def build_analysis_prompt(transcript: str) -> str:
    return f"""Eres un experto en creación de contenido viral para redes sociales con más de 10 años de experiencia en el nicho de fitness y suplementos deportivos. Analiza el siguiente guion de un video de TikTok.

GUION:
\"\"\"
{transcript}
\"\"\"

Responde SOLO con un JSON válido (sin markdown, sin ```), con esta estructura exacta:

{{
  "hook": {{
    "text": "texto exacto de los primeros 3 segundos del guion",
    "type": "tipo de hook (pregunta, dato impactante, controversia, antes/después, historia personal, desafío, mito, promesa)",
    "score": 8,
    "explanation": "por qué este hook funciona o no funciona"
  }},
  "structure": {{
    "sections": [
      {{"name": "Hook", "duration": "0-3s", "content": "descripción breve"}},
      {{"name": "Desarrollo", "duration": "3-Xs", "content": "descripción breve"}},
      {{"name": "CTA", "duration": "X-Ys", "content": "descripción breve"}}
    ],
    "rhythm": "rápido/medio/lento"
  }},
  "virality_score": {{
    "score": 7,
    "justification": "explicación del score",
    "positive_factors": ["factor 1", "factor 2"],
    "negative_factors": ["factor 1"]
  }},
  "persuasion_elements": [
    {{"technique": "nombre de la técnica", "usage": "cómo se usa en el guion", "effectiveness": "alta/media/baja"}}
  ]
}}

IMPORTANTE: Evalúa la viralidad del 1 al 10, donde 10 es máximo potencial viral."""


def analyze_script(transcript: str, client: OpenAI = None, api_key: str = None) -> dict:
    """Analyze a TikTok script using GPT-4o. Returns parsed analysis dict."""
    if client is None:
        client = OpenAI(api_key=api_key)

    prompt = build_analysis_prompt(transcript)

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]

    return json.loads(raw_text)
