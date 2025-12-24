# generator/audio/silence.py

from moviepy.editor import AudioClip

def generate_silence(duracion: float):
    return AudioClip(
        make_frame=lambda t: 0,
        duration=duracion,
        fps=44100
    )
