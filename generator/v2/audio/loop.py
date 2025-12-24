# generator/v2/audio/loop.py

from moviepy.editor import concatenate_audioclips


def build_loop_clips(audio, duration: float):
    """
    Devuelve la lista de subclips necesarios para alcanzar duration.
    Función PURA → 100% testeable.
    """
    clips = []
    t = 0.0

    while t < duration:
        sub = audio.subclip(0, min(audio.duration, duration - t))
        clips.append(sub)
        t += sub.duration

    return clips


def audio_loop(audio, duration: float):
    """
    Wrapper real que usa MoviePy.
    NO se testea directamente.
    """
    clips = build_loop_clips(audio, duration)
    return concatenate_audioclips(clips)
