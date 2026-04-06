from openai import OpenAI

SYSTEM_PROMPT = """Eres un experto en creación de contenido viral para redes sociales con más de 10 años de experiencia en fitness y suplementos deportivos.

Tu trabajo es refinar guiones de TikTok según las instrucciones del usuario. Responde SIEMPRE y SOLO con el guion modificado completo, sin explicaciones ni comentarios adicionales.

Mantén el guion natural, como si alguien lo dijera frente a cámara. Incluye indicaciones de cámara entre [corchetes] cuando sea útil. Escribe en español neutro."""


def build_chat_prompt(original_transcript: str, analysis_summary: str, current_script: str, chat_history: list[dict], user_message: str) -> list[dict]:
    messages = [
        {
            "role": "system",
            "content": f"""{SYSTEM_PROMPT}

CONTEXTO:
- Guion original del video viral: {original_transcript}
- Análisis: {analysis_summary}
- Guion adaptado actual: {current_script}""",
        }
    ]
    for msg in chat_history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})
    return messages


def chat_refine(original_transcript: str, analysis_summary: str, current_script: str, chat_history: list[dict], user_message: str, client: OpenAI = None, api_key: str = None) -> str:
    if client is None:
        client = OpenAI(api_key=api_key)
    messages = build_chat_prompt(original_transcript, analysis_summary, current_script, chat_history, user_message)
    response = client.chat.completions.create(model="gpt-4o", max_tokens=1500, messages=messages)
    return response.choices[0].message.content.strip()
