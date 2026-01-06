# generator/bots/pin_comments/ai/generator.py

from typing import Dict
import os
from openai import OpenAI
from dotenv import load_dotenv

from generator.v3.bots.pin_comment.prompts.base import PIN_COMMENT_BASE_PROMPT

load_dotenv("config/.env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_pin_comment(context: Dict) -> Dict:
    """
    Genera el texto del pin comment usando IA.
    NO sabe de YouTube, DB ni workers.
    """
    prompt = PIN_COMMENT_BASE_PROMPT.format(
        channel_name=context["channel_name"],
        video_tipo=context["video_tipo"],
    )

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

        text = response.choices[0].message.content.strip()

    except Exception:
        text = (
            "🙏 Que este momento te acompañe hoy.\n"
            "Si lo deseas, deja tu intención y oremos juntos."
        )

    return {
        "text": text,
        "model": model,
        "prompt_id": "pin_comment_base",
        "prompt_version": "1.0",
    }
