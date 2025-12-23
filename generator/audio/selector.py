import os
import random
from moviepy.editor import AudioFileClip, CompositeAudioClip
from generator.audio.loop import audio_loop
from db.connection import get_connection
from generator.audio.tts_edge import generar_voz_edge
from generator.audio.silence import generar_silencio
from moviepy.editor import concatenate_audioclips
import uuid


def crear_audio(
    duracion: float,
    musica_fija: str | None = None,
    ventana: int = 20,
    usar_tts: bool = False,
    texto_tts: str | None = None
):

    # -------------------------------------------------
    # 🎵 1. Cargar música base (siempre)
    # -------------------------------------------------
    audios_disponibles = [
        f for f in os.listdir("musica")
        if f.lower().endswith(".mp3")
    ]

    if not audios_disponibles:
        raise RuntimeError("No hay audios en musica/")

    if musica_fija:
        musica_clip, musica_usada = _cargar_audio(musica_fija, duracion)
    else:
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
            candidatas = audios_disponibles

        archivo = random.choice(candidatas)
        musica_clip, musica_usada = _cargar_audio(archivo, duracion)

    # -------------------------------------------------
    # 🔊 2. Si NO hay TTS → devolver solo música
    # -------------------------------------------------
    if not usar_tts:
        return musica_clip, musica_usada

    # -------------------------------------------------
    # 🔊 3. Generar voz TTS
    # -------------------------------------------------
    if not texto_tts:
        raise ValueError("usar_tts=True requiere texto_tts")

    tts_path = f"tmp/tts_{uuid.uuid4().hex}.wav"

    voz_clip = generar_voz_edge(
        texto=texto_tts,
        salida_wav=tts_path
    )

    # Ajustar duración de la voz
    if voz_clip.duration < duracion:
        silencio = generar_silencio(duracion - voz_clip.duration)
        voz_clip = concatenate_audioclips([voz_clip, silencio])
    else:
        voz_clip = voz_clip.subclip(0, duracion)

    # -------------------------------------------------
    # 🔀 4. Mezclar voz + música
    # -------------------------------------------------
    musica_clip = musica_clip.volumex(0.35)   # fondo
    voz_clip = voz_clip.volumex(1.0)           # protagonista

    audio_final = CompositeAudioClip([musica_clip, voz_clip])

    return audio_final, musica_usada



def _cargar_audio(archivo: str, duracion: float):
    ruta = os.path.join("musica", archivo)
    audio = AudioFileClip(ruta)

    if audio.duration < duracion:
        audio = audio_loop(audio, duration=duracion)
    else:
        inicio = random.uniform(0, max(0, audio.duration - duracion))
        audio = audio.subclip(inicio, inicio + duracion)

    return audio, archivo
