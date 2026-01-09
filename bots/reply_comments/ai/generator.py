# bots/reply_comment/ai/generator.py

from typing import Dict
from openai import OpenAI
import os
from dotenv import load_dotenv

from bots.reply_comments.prompts.base import BASE_PROMPT

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = "gpt-4o-mini"
PROMPT_VERSION = "1.0"


def generate_reply(context: Dict) -> Dict:
    prompt = BASE_PROMPT.format(
        channel_name=context["channel_name"],
        user_comment=context["user_comment"],
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.choices[0].message.content.strip()

    except Exception:
        text = "Gracias por unirte en oración. Que el Señor te bendiga 🙏"

    return {
        "text": text,
        "model": MODEL,
        "prompt_version": PROMPT_VERSION,
    }
