# generator/v2/content/layout/duration.py

def calcular_duracion_bloque(
    texto: str,
    *,
    tts_enabled: bool = False,
) -> float:
    """
    Duración sugerida de un bloque visual.

    - Sin TTS: duración editorial (como hasta ahora)
    - Con TTS: duración basada en lectura aproximada
    """

    lineas = [l for l in texto.splitlines() if l.strip()]
    n_lineas = len(lineas)

    if not tts_enabled:
        # === comportamiento actual ===
        if n_lineas <= 7:
            return 20.0
        elif n_lineas <= 12:
            return 28.0
        else:
            return 35.0

    # === MODO TTS ===
    palabras = sum(len(l.split()) for l in lineas)

    # velocidad lectura TTS ≈ 2.2 palabras/seg
    duracion_lectura = palabras / 2.2

    # límites editoriales (muy importantes)
    return max(3.5, min(duracion_lectura, 8.0))