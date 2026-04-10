import json
from openai import OpenAI


def extract_viral_structure(original_transcript: str, analysis_summary: str, client: OpenAI) -> str:
    """Step 1: Extract ONLY the viral structure/format from the original video."""
    response = client.chat.completions.create(
        model=getattr(client, '_model', 'gpt-4o'),
        max_tokens=800,
        messages=[{"role": "user", "content": f"""Analiza este guion viral y extrae SOLO su estructura y técnicas. NO menciones el producto ni el tema del video.

GUION:
\"\"\"{original_transcript}\"\"\"

ANÁLISIS: {analysis_summary}

Responde con:
1. FORMATO: ¿Qué formato usa? (ej: "problema + solución", "lista de 3 tips", "mito vs realidad", "tutorial paso a paso")
2. HOOK: ¿Qué técnica usa para atrapar en los primeros 3 segundos?
3. ESTRUCTURA: Describe la estructura paso a paso SIN mencionar el tema
4. TONO: ¿Cómo habla? (educativo, energético, casual, autoritario)
5. DURACIÓN: Duración aproximada y ritmo
6. TÉCNICAS DE RETENCIÓN: ¿Qué hace para que sigas viendo?"""}],
    )
    return response.choices[0].message.content.strip()


def research_product(product_or_topic: str, client: OpenAI) -> str:
    """Step 2: Deep research the product like an expert would."""
    response = client.chat.completions.create(
        model=getattr(client, '_model', 'gpt-4o'),
        max_tokens=1000,
        messages=[{"role": "user", "content": f"""Eres un experto en suplementos deportivos y fitness con conocimiento profundo basado en evidencia científica.

Haz una investigación completa de: {product_or_topic}

Responde con TODA la información relevante para crear contenido de valor:
1. ¿Qué es exactamente?
2. ¿Qué hace REALMENTE en el cuerpo? (mecanismo de acción simplificado)
3. ¿Qué beneficios tiene respaldados por evidencia?
4. ¿Qué NO hace? (mitos comunes que debes desmentir)
5. ¿Cómo se toma correctamente? (dosis, horario, con qué combinarlo)
6. ¿Para quién es ideal?
7. ¿Qué errores comete la gente al usarlo?
8. Datos interesantes o sorprendentes que servirían para un video viral

IMPORTANTE: Solo incluye información que sea correcta y verificable. Si algo es debatible, menciónalo."""}],
    )
    return response.choices[0].message.content.strip()


def build_creation_prompt(viral_structure: str, product_or_topic: str, product_research: str) -> str:
    return f"""Eres un creador de contenido viral para TikTok. Vas a crear 5 guiones sobre {product_or_topic}.

ESTRUCTURA VIRAL A SEGUIR (extraída de un video exitoso):
{viral_structure}

INVESTIGACIÓN DEL PRODUCTO (usa SOLO esta información para el contenido):
{product_research}

CREA 5 GUIONES que:
1. Sigan la MISMA estructura viral descrita arriba (mismo formato, mismo ritmo, mismas técnicas de retención)
2. El contenido sea 100% sobre {product_or_topic} con información de la investigación
3. Cada uno tenga un HOOK DIFERENTE — los 5 hooks más potentes y virales posibles
4. Suenen natural, como una persona real hablando a cámara con convicción
5. Incluyan indicaciones de cámara entre [corchetes]
6. Estén en español neutro
7. Tengan la misma duración aproximada que el formato original
8. Aporten VALOR REAL — que alguien que vea el video aprenda algo útil y correcto

⚠️ PROHIBIDO:
- Inventar datos numéricos o porcentajes sin base
- Copiar frases del video original cambiando solo el nombre del producto
- Afirmar cosas que no están en la investigación del producto
- Contenido genérico que no aporta valor real

Responde SOLO con un JSON array (sin markdown, sin ```):
[
  {{"version_number": 1, "hook_style": "descripción del hook", "script": "guion completo"}},
  {{"version_number": 2, "hook_style": "descripción del hook", "script": "guion completo"}},
  {{"version_number": 3, "hook_style": "descripción del hook", "script": "guion completo"}},
  {{"version_number": 4, "hook_style": "descripción del hook", "script": "guion completo"}},
  {{"version_number": 5, "hook_style": "descripción del hook", "script": "guion completo"}}
]"""


def generate_versions(
    original_transcript: str,
    analysis_summary: str,
    product_or_topic: str,
    client: OpenAI = None,
    api_key: str = None,
    groq_api_key: str = None,
) -> list[dict]:
    """Generate 5 adapted script versions. Uses Groq first (free), OpenAI fallback."""
    if groq_api_key:
        try:
            client = OpenAI(api_key=groq_api_key, base_url="https://api.groq.com/openai/v1")
            # Test with Groq model
            client._model = "llama-3.3-70b-versatile"
        except Exception:
            pass
    if client is None and api_key:
        client = OpenAI(api_key=api_key)
    if client is None:
        raise Exception("No API key for generation")

    # Step 1: Extract viral structure (no product mentioned)
    viral_structure = extract_viral_structure(original_transcript, analysis_summary, client)

    # Step 2: Deep research the product
    product_research = research_product(product_or_topic, client)

    # Step 3: Create 5 guiones using structure + research
    prompt = build_creation_prompt(viral_structure, product_or_topic, product_research)

    response = client.chat.completions.create(
        model=getattr(client, '_model', 'gpt-4o'),
        max_tokens=6000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.choices[0].message.content.strip()

    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]

    return json.loads(raw_text)
