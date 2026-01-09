# adapter/audio_fingerprint_adapter.py
from generator.audio.selector import crear_audio
from generator.fingerprinter import generar_fingerprint_contenido
from db.repositories.video_repo import fingerprint_existe_ultimos_dias

    
def resolver_audio_y_fingerprint_v3(
    *,
    tipo: str,
    texto: str,
    imagen_usada: str | None,
    audio_duracion: float,
    usar_tts: bool,
    max_intentos: int = 5,
    audio_inicial: tuple | None = None,
):
  
    if audio_inicial:
        audio, musica_usada = audio_inicial
    else:
        audio, musica_usada = crear_audio(
            audio_duracion,
            None,
            usar_tts=usar_tts,
            texto_tts=texto,
        )

    duracion_norm = int(round(audio_duracion))

    fingerprint = generar_fingerprint_contenido(
        tipo=tipo,
        texto=texto,
        imagen=imagen_usada,
        musica=musica_usada,
        duracion=duracion_norm,
    )

    intentos = 0
    while fingerprint_existe_ultimos_dias(fingerprint) and intentos < max_intentos:
        print("⚠ Contenido duplicado (120 días) → cambiando música")

        audio, musica_usada = crear_audio(
            audio_duracion,
            None,
            usar_tts=usar_tts,
            texto_tts=texto,
        )

        fingerprint = generar_fingerprint_contenido(
            tipo=tipo,
            texto=texto,
            imagen=imagen_usada,
            musica=musica_usada,
            duracion=duracion_norm,
        )

        intentos += 1

    return audio, musica_usada, fingerprint
