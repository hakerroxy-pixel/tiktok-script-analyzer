from anthropic import Anthropic


def build_adaptation_prompt(original_transcript: str, analysis_summary: str, product_or_topic: str) -> str:
    return f"""Eres un experto en creación de contenido viral para redes sociales con más de 10 años de experiencia en fitness y suplementos deportivos. Tu tarea es adaptar un guion viral exitoso a un producto o tema específico.

GUION ORIGINAL:
\"\"\"
{original_transcript}
\"\"\"

ANÁLISIS DEL GUION:
{analysis_summary}

PRODUCTO/TEMA A ADAPTAR: {product_or_topic}

Reescribe el guion adaptándolo al producto/tema indicado. Reglas:
1. Mantén la MISMA estructura que hace viral al original (hook, ritmo, CTA)
2. Usa el mismo tipo de hook pero adaptado al nuevo producto/tema
3. Mantén la misma duración aproximada
4. El guion debe sonar natural, como si alguien lo dijera frente a cámara
5. Escribe en español neutro
6. Incluye indicaciones de cámara entre [corchetes] cuando sea útil

Responde SOLO con el guion adaptado, sin explicaciones adicionales."""


def adapt_script(
    original_transcript: str,
    analysis_summary: str,
    product_or_topic: str,
    client: Anthropic = None,
    api_key: str = None,
) -> str:
    """Adapt a viral script to a specific product/topic using Claude. Returns adapted script text."""
    if client is None:
        client = Anthropic(api_key=api_key)

    prompt = build_adaptation_prompt(original_transcript, analysis_summary, product_or_topic)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text.strip()
