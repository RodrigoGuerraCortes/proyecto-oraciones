# generator/audio/selector.py
import os
import random
from moviepy.editor import AudioFileClip

from historial import cargar_historial
from generar_aleatoridad import elegir_musica_no_reciente

from generator.audio.loop import audio_loop


def crear_audio(duracion: float, musica_fija: str | None = None):
    """
    Devuelve: (audio_clip, musica_usada)
    """
    historial = cargar_historial()

    audios_disponibles = [
        f for f in os.listdir("musica")
        if f.lower().endswith(".mp3")
    ]
    if not audios_disponibles:
        raise RuntimeError("No hay audios .mp3 en carpeta musica/")

    # Música fija
    if musica_fija:
        ruta = os.path.join("musica", musica_fija)
        print(f"[AUDIO] Usando música fija: {musica_fija}")

        audio = AudioFileClip(ruta)
        if audio.duration < duracion:
            print("[AUDIO] Música corta → loop automático")
            audio = audio_loop(audio, duration=duracion)
        else:
            audio = audio.subclip(0, duracion)

        return audio, musica_fija

    # Música aleatoria no reciente
    intentos = 0
    while intentos < 3:
        try:
            archivo = elegir_musica_no_reciente(historial)
            ruta = os.path.join("musica", archivo)
            print(f"[AUDIO] Música seleccionada (no reciente): {archivo}")

            audio = AudioFileClip(ruta)
            dur_audio = audio.duration

            if dur_audio < duracion:
                print("[AUDIO] Música corta → loop")
                audio = audio_loop(audio, duration=duracion)
            else:
                inicio = random.uniform(0, max(0, dur_audio - duracion))
                audio = audio.subclip(inicio, inicio + duracion)

            return audio, archivo

        except Exception as e:
            print(f"[AUDIO ERROR] {e}")
            intentos += 1

    # Fallback
    archivo = audios_disponibles[0]
    ruta = os.path.join("musica", archivo)
    print("[AUDIO] Fallback → primer mp3 disponible")
    audio = AudioFileClip(ruta)
    if audio.duration < duracion:
        audio = audio_loop(audio, duration=duracion)
    else:
        audio = audio.subclip(0, duracion)

    return audio, archivo
