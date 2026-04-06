import json
from openai import OpenAI


# Product knowledge base — real info about supplements
PRODUCT_INFO = {
    "creatina": "Creatina monohidrato. Aumenta fuerza, potencia y rendimiento en entrenamientos de alta intensidad. Mejora la recuperación muscular. El suplemento más estudiado científicamente. Dosis: 5g/día. Se puede tomar a cualquier hora, no importa el timing. Fase de carga opcional (20g/día por 5 días). Retiene agua intracelular (no hincha). Se mezcla con agua o jugo. Ideal para fuerza, hipertrofia y deportes explosivos. Beneficios reales: más repeticiones, más fuerza, mejor recuperación entre series.",
    "preentreno": "Pre-entreno / Preentreno. Aumenta energía, enfoque mental y rendimiento durante el entrenamiento. Ingredientes comunes: cafeína (150-300mg), beta-alanina (causa hormigueo en la piel, es normal), citrulina (bombeo muscular). Se toma 20-30 min antes de entrenar con agua. NO tomar después de las 6pm porque contiene cafeína. Efecto: energía explosiva, mejor conexión mente-músculo, más resistencia.",
    "psychotic": "Psychotic de Insane Labz. Pre-entreno de alta estimulación. Contiene cafeína, beta-alanina, creatina, AMPiberry. Conocido por su potencia extrema — media cucharada es suficiente para principiantes. Efecto: energía intensa que dura 2-3 horas, enfoque láser, bombeo. Para usuarios avanzados. Sabores: Gummy Candy, Grape, Cotton Candy. NO mezclar con café.",
    "proteina": "Proteína en polvo (whey protein). 20-30g de proteína por servicio. Se toma después de entrenar (ventana anabólica) o como snack entre comidas. Se mezcla con agua o leche. Ayuda a alcanzar el requerimiento proteico diario (1.6-2.2g/kg). Sabores variados. Tipos: concentrada (más económica), aislada (menos lactosa), hidrolizada (absorción rápida).",
    "mk677": "MK-677 (Ibutamoren). Secretagogo de hormona de crecimiento oral. Aumenta GH y IGF-1 naturalmente. Beneficios reales: mejor calidad de sueño profundo, recuperación muscular acelerada, aumento de apetito, piel y cabello más saludables, mejor densidad ósea. Se toma 1 vez al día, preferible antes de dormir. No es un esteroide ni un SARM. Ciclos de 8-12 semanas. Efecto secundario principal: aumento de apetito y retención de agua temporal.",
    "citrulina": "L-Citrulina / Citrulina Malato. Precursor del óxido nítrico. Se toma 20-30 min ANTES de entrenar con agua. Dosis: 6-8g. Efecto real: vasodilatación (venas más marcadas), mejor bombeo muscular, mayor flujo de sangre a los músculos, reduce fatiga y dolor muscular post-entreno, mejora resistencia. Funciona mejor en ayunas o con el estómago vacío. No tiene sabor. Se puede combinar con preentreno.",
    "omega 3": "Omega 3 (EPA/DHA). Ácidos grasos esenciales que el cuerpo NO produce. Se toma con comidas que contengan grasa para mejor absorción. Dosis: 2-3g/día. Beneficios reales: reduce inflamación, mejora salud cardiovascular, lubrica articulaciones, mejora función cerebral, ayuda a recuperación muscular. Para deportistas: reduce dolor articular y muscular post-entreno.",
    "bcaa": "BCAAs (aminoácidos de cadena ramificada). Leucina, isoleucina, valina. Se toman DURANTE el entrenamiento mezclados con agua. Reducen fatiga durante sesiones largas. Preservan masa muscular en déficit calórico (dieta de corte). Dan sabor al agua del gym. Dosis: 5-10g durante el entreno.",
    "quemador": "Quemador de grasa / Termogénico. Contiene cafeína, extracto de té verde, L-carnitina. Se toma en ayunas o 30 min antes de entrenar. Acelera metabolismo y aumenta quema calórica. IMPORTANTE: solo funciona SI estás en déficit calórico. No es mágico. Complementa dieta y ejercicio. No tomar después de las 4pm.",
    "glutamina": "L-Glutamina. Aminoácido más abundante en el cuerpo. Se toma después de entrenar o antes de dormir. Dosis: 5-10g/día. Mejora recuperación muscular, fortalece sistema inmune, mejora salud intestinal. Ideal en periodos de entrenamiento intenso donde el cuerpo se desgasta más.",
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

    return f"Investiga sobre '{product_or_topic}' y asegúrate de que todo lo que digas sobre este producto/tema sea 100% correcto y verificable. NO inventes beneficios ni propiedades que no tenga."


def build_multi_version_prompt(original_transcript: str, analysis_summary: str, product_or_topic: str) -> str:
    product_context = get_product_context(product_or_topic)

    return f"""Eres un creador de contenido viral experto en fitness y suplementos deportivos.

PASO 1 — ANALIZA EL VIDEO ORIGINAL:
El siguiente guion se hizo viral. Tu trabajo es entender POR QUÉ funcionó:
\"\"\"
{original_transcript}
\"\"\"
Análisis: {analysis_summary}

Identifica SOLO la estructura y técnicas virales:
- ¿Cómo atrapa la atención en los primeros 3 segundos?
- ¿Qué formato usa? (lista numerada, problema-solución, mito vs realidad, tutorial, storytelling, etc.)
- ¿Qué ritmo tiene? ¿Cómo mantiene la atención?
- ¿Qué CTA usa al final?

PASO 2 — CONOCE EL NUEVO PRODUCTO:
Producto: {product_or_topic}
{product_context}

PASO 3 — CREA 5 GUIONES NUEVOS:
Usa la ESTRUCTURA y FORMATO del video original pero con CONTENIDO 100% NUEVO sobre {product_or_topic}.

⚠️ REGLA CRÍTICA: NO copies afirmaciones del video original y reemplaces el nombre del producto. Eso es lo que NUNCA debes hacer. Ejemplo de lo que está MAL:
- Original dice "el omega 3 se absorbe 300% mejor con grasas" → NO digas "la citrulina se absorbe 300% mejor con carbohidratos"
- Original dice "3 mejores horarios para tomar omega 3" → NO hagas "3 mejores horarios para tomar citrulina" con la misma lógica

Lo que SÍ debes hacer:
- Original usa formato "Si usas X y no ves resultados, es porque..." → USA ese mismo formato pero con información REAL de {product_or_topic}
- Original da 3 tips numerados → TÚ da 3 tips numerados pero sobre {product_or_topic} con info correcta
- Original usa un tono educativo → Mantén ese tono

Cada versión debe:
- Tener un HOOK DIFERENTE — los 5 hooks más potentes y virales posibles para {product_or_topic}
- Usar info 100% REAL del producto (ver PASO 2)
- Sonar natural, como hablando a cámara
- Tener la misma duración aproximada que el original
- Incluir indicaciones de cámara entre [corchetes]
- Estar en español neutro

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
