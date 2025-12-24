# generator/v2/audio/music_selector.py

import os
import random
from moviepy.editor import AudioFileClip
from generator.v2.audio.loop import audio_loop

MUSIC_DIR = "musica"


def select_music(duration: float, fixed: str | None = None):
    files = [
        f for f in os.listdir(MUSIC_DIR)
        if f.lower().endswith(".mp3")
    ]

    if not files:
        raise RuntimeError("No hay música disponible")

    chosen = fixed if fixed else random.choice(files)
    path = os.path.join(MUSIC_DIR, chosen)

    audio = AudioFileClip(path)

    if audio.duration < duration:
        audio = audio_loop(audio, duration)
    else:
        audio = audio.subclip(0, duration)

    return audio, chosen
