from typing import Dict
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv("config/.env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BASE_PROMPT = """
Eres el community manager de un canal católico en YouTube.

Objetivo:
Generar UN comentario de primer nivel para un video,
con tono respetuoso, espiritual y cercano.

Contexto del canal:
- Nombre: {channel_name}
- Estilo: católico, sobrio, profesional
- Audiencia: personas que buscan oración, consuelo y esperanza

Contexto del video:
- Tipo: {video_tipo} (puede ser "oración" o "salmo")

Guía según el tipo de video:
- Si el video es una ORACIÓN:
  - Enfoca el comentario en la cercanía con Dios
  - Invita a presentar intenciones o necesidades personales
  - Usa un tono de acompañamiento y consuelo

- Si el video es un SALMO:
  - Enfoca el comentario en la confianza en el Señor y su Palabra
  - Invita a reflexionar desde el corazón y a orar con el Salmo
  - Evita un tono intelectual o de análisis bíblico

Instrucciones:
- Máximo 2 líneas
- Incluir una invitación suave a comentar o compartir una intención
- NO usar hashtags
- NO emojis excesivos (máx 1)
- Lenguaje claro, cálido y devocional
- No sonar comercial ni genérico

Si se proporciona contenido del video, úsalo para generar un comentario más específico,
sin repetir literalmente el texto.

Devuelve SOLO el texto del comentario.
""".strip()


def generate_ai_comment(context: Dict) -> Dict:
    prompt = BASE_PROMPT.format(
        channel_name=context["channel_name"],
        video_tipo=context["video_tipo"],
    )

    # Texto base opcional
    if context.get("video_texto_base"):
        prompt += (
            "\n\nContenido del video:\n"
            f"{context['video_texto_base'][:500]}"
        )

    model = "gpt-4o-mini"

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        texto_corto = response.choices[0].message.content.strip()

    except Exception:
        texto_corto = (
            "🙏 Que esta oración te acompañe hoy.\n"
            "Si lo deseas, deja tu intención y oremos juntos."
        )

    return {
        "text": texto_corto,
        "model": model,
        "prompt_version": "v1",
    }
