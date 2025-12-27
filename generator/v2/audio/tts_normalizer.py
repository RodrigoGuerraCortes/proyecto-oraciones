# generator/v2/audio/tts_normalizer.py

import re


def normalize_text_for_tts(text: str) -> str:
    """
    Normaliza texto visual para lectura TTS (Edge TTS).
    Mejora prosodia, pausas y naturalidad.
    NO afecta el texto visual.
    """

    if not text:
        return text

    t = text.strip()

    # ---------------------------------------------
    # 1) Normalizar saltos de línea
    # ---------------------------------------------
    # Doble salto → pausa larga (reflexión)
    t = re.sub(r"\n\s*\n+", '<break time="800ms"/>', t)

    # Salto simple → pausa media
    t = re.sub(r"\n+", '<break time="400ms"/>', t)

    # ---------------------------------------------
    # 2) Asegurar puntuación antes de pausas
    # ---------------------------------------------
    # Evita frases "cortadas" sin cierre semántico
    t = re.sub(
        r'([a-zA-ZáéíóúÁÉÍÓÚñÑ])\s*(<break)',
        r'\1. \2',
        t
    )

    # ---------------------------------------------
    # 3) Normalizar espacios
    # ---------------------------------------------
    t = re.sub(r"\s+", " ", t)

    # ---------------------------------------------
    # 4) Asegurar cierre final
    # ---------------------------------------------
    if not re.search(r"[.!?]$", t):
        t += "."

    return t
