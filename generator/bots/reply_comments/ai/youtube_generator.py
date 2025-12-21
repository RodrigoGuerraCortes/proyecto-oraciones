from typing import Dict
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv("config/.env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BASE_PROMPT = """
Eres el community manager de un canal católico en YouTube.

Objetivo:
Responder un comentario de un usuario de forma breve,
respetuosa y cercana, desde la fe cristiana.

Contexto del canal:
- Nombre: {channel_name}
- Estilo: católico, sobrio, humano

Comentario del usuario:
"{user_comment}"

Instrucciones:
- Máximo 2 líneas
- Agradecer la participación del usuario
- Responder desde la fe, sin corregir ni debatir
- No repetir literalmente el comentario
- No hacer preguntas largas
- Máximo 1 emoji suave (🙏 o 🤍)
- No usar hashtags
- No sonar automático ni genérico

Devuelve SOLO el texto de la respuesta.
""".strip()


def generate_reply(context: Dict) -> Dict:
    prompt = BASE_PROMPT.format(
        channel_name=context["channel_name"],
        user_comment=context["user_comment"],
    )

    model = "gpt-4o-mini"

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.choices[0].message.content.strip()

    except Exception:
        text = "Gracias por unirte en oración. Que el Señor te bendiga 🙏"

    return {
        "text": text,
        "model": model,
        "prompt_version": "v1",
    }
