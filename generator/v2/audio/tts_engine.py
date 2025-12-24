# generator/v2/audio/tts_engine.py

import os
import subprocess
import sys
from moviepy.editor import AudioFileClip

DEFAULT_VOICE = "es-MX-JorgeNeural"
DEFAULT_RATE = "-15%"
DEFAULT_PITCH = "-2Hz"


def generate_voice(
    texto: str,
    salida_wav: str,
    voz: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE,
    pitch: str = DEFAULT_PITCH
) -> AudioFileClip:
    if not texto.strip():
        raise ValueError("Texto TTS vacío")

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
