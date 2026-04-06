import json
from openai import OpenAI


# Product knowledge base — real info about supplements
PRODUCT_INFO = {
    "creatina": "Creatina monohidrato. Aumenta fuerza, potencia y rendimiento en entrenamientos de alta intensidad. Mejora la recuperación muscular. El suplemento más estudiado científicamente. Dosis: 5g/día. Retiene agua intracelular (no subcutánea). Ideal para fuerza, hipertrofia y deportes explosivos.",
    "preentreno": "Pre-entreno / Preentreno. Aumenta energía, enfoque mental y rendimiento durante el entrenamiento. Contiene cafeína, beta-alanina (hormigueo), citrulina (bombeo muscular). Se toma 20-30 min antes de entrenar. Efecto: energía explosiva, mejor conexión mente-músculo.",
    "psychotic": "Psychotic de Insane Labz. Pre-entreno de alta estimulación. Contiene cafeína, beta-alanina, creatina, AMPiberry. Conocido por su potencia extrema. Efecto: energía intensa, enfoque láser. Para usuarios avanzados que buscan el máximo rendimiento.",
    "proteina": "Proteína en polvo (whey protein). Ayuda a la recuperación y crecimiento muscular post-entrenamiento. 20-30g de proteína por servicio. Se toma después de entrenar o como snack proteico. Sabores variados. Ideal para completar requerimiento proteico diario.",
    "mk677": "MK-677 (Ibutamoren). Secretagogo de hormona de crecimiento. Aumenta GH y IGF-1 naturalmente. Beneficios: mejor sueño, recuperación muscular, aumento de apetito, piel más saludable. No es un esteroide. Ciclos de 8-12 semanas.",
    "citrulina": "L-Citrulina / Citrulina Malato. Precursor del óxido nítrico. Mejora el flujo sanguíneo y el bombeo muscular. Reduce fatiga durante el entrenamiento. Dosis: 6-8g antes de entrenar. Efecto: venas más marcadas, mayor resistencia.",
    "omega 3": "Omega 3 (EPA/DHA). Ácidos grasos esenciales. Antiinflamatorio natural. Beneficios: salud cardiovascular, articulaciones, cerebro, recuperación muscular. Dosis: 2-3g/día. Reduce dolor articular en deportistas.",
    "bcaa": "BCAAs (aminoácidos de cadena ramificada). Leucina, isoleucina, valina. Reducen fatiga durante el entrenamiento. Ayudan a preservar masa muscular en déficit calórico. Se toman durante o después del entrenamiento.",
    "quemador": "Quemador de grasa / Termogénico. Acelera el metabolismo. Contiene cafeína, extracto de té verde, L-carnitina. Aumenta la quema calórica. Se usa junto a dieta y ejercicio. No es mágico — complementa el déficit calórico.",
    "glutamina": "L-Glutamina. Aminoácido más abundante en el cuerpo. Mejora recuperación muscular y salud intestinal. Fortalece el sistema inmune. Dosis: 5-10g/día. Ideal en periodos de entrenamiento intenso.",
}


def get_product_context(product_or_topic: str) -> str:
    """Find relevant product info from the knowledge base."""
    product_lower = product_or_topic.lower()
    matches = []
    for key, info in PRODUCT_INFO.items():
        if key in product_lower or product_lower in key:
            matches.append(info)

    if matches:
        return "\n".join(matches)

    # No exact match — return generic instruction
    return f"Investiga sobre '{product_or_topic}' y asegúrate de que todo lo que digas sobre este producto/tema sea 100% correcto y verificable. NO inventes beneficios ni propiedades que no tenga."


def build_multi_version_prompt(original_transcript: str, analysis_summary: str, product_or_topic: str) -> str:
    product_context = get_product_context(product_or_topic)

    return f"""Eres un experto en creación de contenido viral para redes sociales con más de 10 años de experiencia en fitness y suplementos deportivos. Conoces a fondo cada suplemento, sus beneficios REALES y sus limitaciones.

GUION ORIGINAL VIRAL (este video se hizo viral, analiza por qué):
\"\"\"
{original_transcript}
\"\"\"

ANÁLISIS DE POR QUÉ FUNCIONA: {analysis_summary}

PRODUCTO/TEMA A ADAPTAR: {product_or_topic}

INFORMACIÓN REAL DEL PRODUCTO:
{product_context}

INSTRUCCIONES CRÍTICAS:
1. PRIMERO entiende la ESTRUCTURA y TÉCNICAS que hacen viral al guion original (ritmo, transiciones, tensión, CTA, etc.)
2. Luego adapta ESA ESTRUCTURA al producto indicado
3. TODO lo que digas sobre el producto DEBE ser real y correcto. NO inventes beneficios que no tiene. Si el producto no hace algo, NO lo menciones.
4. El guion debe sonar NATURAL, como si alguien lo dijera frente a cámara con convicción
5. Usa la misma duración aproximada que el original

Genera 5 versiones. Cada versión debe:
- Usar la MISMA estructura y técnicas de viralidad del original (parafrasear, NO copiar textualmente)
- Tener un HOOK DIFERENTE — elige los 5 mejores hooks posibles para este producto (NO uses categorías fijas, simplemente crea los 5 hooks más potentes y virales que se te ocurran)
- El cuerpo del guion debe decir lo mismo pero con palabras diferentes en cada versión
- Incluir indicaciones de cámara entre [corchetes]
- Estar en español neutro

Responde SOLO con un JSON array (sin markdown, sin ```):
[
  {{"version_number": 1, "hook_style": "descripción corta del tipo de hook usado", "script": "guion completo aquí"}},
  {{"version_number": 2, "hook_style": "descripción corta del tipo de hook usado", "script": "guion completo aquí"}},
  {{"version_number": 3, "hook_style": "descripción corta del tipo de hook usado", "script": "guion completo aquí"}},
  {{"version_number": 4, "hook_style": "descripción corta del tipo de hook usado", "script": "guion completo aquí"}},
  {{"version_number": 5, "hook_style": "descripción corta del tipo de hook usado", "script": "guion completo aquí"}}
]"""


def generate_versions(
    original_transcript: str,
    analysis_summary: str,
    product_or_topic: str,
    client: OpenAI = None,
    api_key: str = None,
) -> list[dict]:
    """Generate 5 adapted script versions with different hooks. Returns list of dicts."""
    if client is None:
        client = OpenAI(api_key=api_key)

    prompt = build_multi_version_prompt(original_transcript, analysis_summary, product_or_topic)

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=6000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]

    return json.loads(raw_text)
