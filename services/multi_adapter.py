import json
from openai import OpenAI

HOOK_STYLES = ["pregunta", "dato_impactante", "controversia", "historia_personal", "promesa"]

def build_multi_version_prompt(original_transcript: str, analysis_summary: str, product_or_topic: str) -> str:
    return f"""Eres un experto en creación de contenido viral para redes sociales con más de 10 años de experiencia en fitness y suplementos deportivos.

GUION ORIGINAL VIRAL:
\"\"\"
{original_transcript}
\"\"\"

ANÁLISIS: {analysis_summary}

PRODUCTO/TEMA: {product_or_topic}

Genera 5 versiones del guion adaptado al producto/tema. Las 5 versiones deben:
- Ser FIELES al guion original (misma estructura, mismo mensaje, misma duración)
- Cada una usa un HOOK DIFERENTE de estos tipos: pregunta, dato impactante, controversia, historia personal, promesa
- El desarrollo debe estar PARAFRASEADO (decir lo mismo con palabras distintas)
- El CTA se mantiene similar
- Sonar natural, como si alguien lo dijera frente a cámara
- Estar en español neutro
- Incluir indicaciones de cámara entre [corchetes] cuando sea útil

Responde SOLO con un JSON array (sin markdown, sin ```), con esta estructura:
[
  {{"version_number": 1, "hook_style": "pregunta", "script": "guion completo aquí"}},
  {{"version_number": 2, "hook_style": "dato_impactante", "script": "guion completo aquí"}},
  {{"version_number": 3, "hook_style": "controversia", "script": "guion completo aquí"}},
  {{"version_number": 4, "hook_style": "historia_personal", "script": "guion completo aquí"}},
  {{"version_number": 5, "hook_style": "promesa", "script": "guion completo aquí"}}
]"""

def generate_versions(original_transcript: str, analysis_summary: str, product_or_topic: str, client: OpenAI = None, api_key: str = None) -> list[dict]:
    if client is None:
        client = OpenAI(api_key=api_key)
    prompt = build_multi_version_prompt(original_transcript, analysis_summary, product_or_topic)
    response = client.chat.completions.create(model="gpt-4o", max_tokens=6000, messages=[{"role": "user", "content": prompt}])
    raw_text = response.choices[0].message.content.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
    return json.loads(raw_text)
