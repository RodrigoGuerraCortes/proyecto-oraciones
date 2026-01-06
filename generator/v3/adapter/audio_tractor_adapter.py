# generator/v3/adapter/audio_tractor_adapter.py

import os
from moviepy.editor import AudioFileClip
from generator.v3.generator.audio.loop import audio_loop


def crear_audio_tractor_v3(
    *,
    duracion: float,
    music_path: str,
    track: str,
    loop_cfg: dict | None = None,
):
    """
    Audio adapter específico para TRACTOR.

    - Música fija
    - Loop limpio
    - Sin DB
    - Sin random
    - Sin cortes perceptibles
    """

    ruta = os.path.join(music_path, track)
    if not os.path.isfile(ruta):
        raise FileNotFoundError(f"Música no encontrada: {ruta}")

    audio = AudioFileClip(ruta)

    # -------------------------------------------------
    # Loop limpio
    # -------------------------------------------------
    if audio.duration < duracion:
        crossfade = 0
        if loop_cfg:
            crossfade = loop_cfg.get("crossfade_seconds", 0)

        audio = audio_loop(
            audio,
            duration=duracion,
            crossfade=crossfade
        )
    else:
        # Tractor NUNCA corta aleatoriamente:
        audio = audio.subclip(0, duracion)

    return audio, track
