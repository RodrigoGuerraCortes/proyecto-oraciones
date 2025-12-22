# generator/audio/tts_edge.py

import os
import subprocess
from moviepy.editor import AudioFileClip


DEFAULT_VOICE = "es-ES-AlvaroNeural"
DEFAULT_RATE = "-10%"   # más pausado
DEFAULT_PITCH = "+0Hz"


def generar_voz_edge(
    *,
    texto: str,
    salida_wav: str,
    voz: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE,
    pitch: str = DEFAULT_PITCH
) -> AudioFileClip:
    """
    Genera un archivo WAV usando edge-tts y retorna AudioFileClip.
    """

    os.makedirs(os.path.dirname(salida_wav), exist_ok=True)

    cmd = [
        "edge-tts",
        "--voice", voz,
        "--rate", rate,
        "--pitch", pitch,
        "--text", texto,
        "--write-media", salida_wav,
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("Error generando voz con edge-tts") from e

    return AudioFileClip(salida_wav)
