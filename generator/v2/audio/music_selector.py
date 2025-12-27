# generator/v2/audio/music_selector.py

import os
import random
from moviepy.editor import AudioFileClip
from generator.v2.audio.loop import audio_loop

DEFAULT_MUSIC_SKIP = 5.0

def select_music(
    *,
    duration: float,
    base_path: str,
    fixed: str | None = None
):
    files = [
        f for f in os.listdir(base_path)
        if f.lower().endswith(".mp3")
    ]

    if not files:
        raise RuntimeError(f"No hay música en {base_path}")

    chosen = fixed if fixed else random.choice(files)
    path = os.path.join(base_path, chosen)

    audio = load_music_clip(
        path=path,
        duration=duration,
        skip_start=DEFAULT_MUSIC_SKIP,
    )

    return audio, chosen


def load_music_clip(
    *,
    path: str,
    duration: float,
    skip_start: float = 0.0,
):
    clip = AudioFileClip(path)

    # Saltar intro (V1 behavior)
    if skip_start > 0:
        clip = clip.subclip(skip_start)

    # Ajustar a duración exacta del video
    if clip.duration < duration:
        clip = audio_loop(clip, duration)
    else:
        clip = clip.subclip(0, duration)

    return clip
