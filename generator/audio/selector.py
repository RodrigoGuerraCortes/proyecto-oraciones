import os
import random
from moviepy.editor import AudioFileClip
from generator.audio.loop import audio_loop
from db.connection import get_connection


def crear_audio(duracion: float, musica_fija: str | None = None, ventana: int = 20):
    audios_disponibles = [
        f for f in os.listdir("musica")
        if f.lower().endswith(".mp3")
    ]

    if not audios_disponibles:
        raise RuntimeError("No hay audios en musica/")

    if musica_fija:
        return _cargar_audio(musica_fija, duracion)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT musica
                FROM videos
                WHERE musica IS NOT NULL
                ORDER BY fecha_generado DESC
                LIMIT %s
            """, (ventana,))
            usadas = {row['musica'] for row in cur.fetchall()}

    candidatas = [a for a in audios_disponibles if a not in usadas]
    if not candidatas:
        candidatas = audios_disponibles  # fallback consciente

    archivo = random.choice(candidatas)
    return _cargar_audio(archivo, duracion)


def _cargar_audio(archivo: str, duracion: float):
    ruta = os.path.join("musica", archivo)
    audio = AudioFileClip(ruta)

    if audio.duration < duracion:
        audio = audio_loop(audio, duration=duracion)
    else:
        inicio = random.uniform(0, max(0, audio.duration - duracion))
        audio = audio.subclip(inicio, inicio + duracion)

    return audio, archivo
