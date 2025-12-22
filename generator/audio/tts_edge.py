# generator/audio/tts_edge.py

import os
import subprocess
from moviepy.editor import AudioFileClip
import sys


DEFAULT_VOICE = "es-MX-JorgeNeural"
DEFAULT_RATE = "-15%"
DEFAULT_PITCH = "-2Hz"


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
        sys.executable, "-m", "edge_tts",
        f"--voice={voz}",
        f"--rate={rate}",
        f"--pitch={pitch}",
        f"--text={texto}",
        f"--write-media={salida_wav}",
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("Error generando voz con edge-tts") from e

    return AudioFileClip(salida_wav)




def _normalizar_texto_tts(texto: str) -> str:
    """
    Ajustes específicos para TTS (no UI):
    - Fuerza pronunciación correcta de 'Amén'
    """
    return (
        texto
        .replace("Amén", "Amén,")
        .replace("Amen", "Amén,")
        .replace("amen", "Amén,")
    )

