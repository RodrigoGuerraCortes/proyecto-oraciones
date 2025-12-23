# generator/generar_oracion.py

import os
from moviepy.editor import ImageClip
from moviepy.video.fx.fadein import fadein
from generator.image.fondo import crear_fondo
from generator.image.titulo import crear_imagen_titulo
from generator.image.texto import crear_imagen_texto
from generator.audio.selector import crear_audio
from generator.video.composer import componer_video
from generator.content.fingerprinter import generar_fingerprint_contenido
from db.repositories.video_repo import insert_video, fingerprint_existe_ultimos_dias
#from generator.scheduling.slot_resolver import programar_publicacion_exacta
from generator.cleanup import limpiar_temporales
from generator.utils.texto import dividir_en_bloques, calcular_duracion_bloque
from generator.image.decision import decidir_imagen_video
import os
from generator.experiments.voice_ab import decidir_tts_para_video

ORACION_LINEAS_MAX = 10
CTA_DUR = 5
TTS_PORCENTAJE_ORACION = 0.20

def generar_oracion(
    *,
    video_id,
    path_in: str,
    path_out: str,
    imagen_fija=None,
    musica_fija=None,
    modo_test=False,
    force_tts: bool | None = None
):
    with open(path_in, "r", encoding="utf-8") as f:
        texto = f.read()

    base = os.path.splitext(os.path.basename(path_in))[0]
    titulo = base.replace("_", " ").title()

    lineas = [l for l in texto.splitlines() if l.strip()]

    if modo_test:
        bloques = [texto]
        dur_total = 2
        duraciones = [2]
    else:
        if len(lineas) > ORACION_LINEAS_MAX:
            bloques = dividir_en_bloques(texto, ORACION_LINEAS_MAX)
            duraciones = [calcular_duracion_bloque(b) for b in bloques]
            dur_total = sum(duraciones)
        else:
            bloques = [texto]
            dur_total = calcular_duracion_bloque(texto)
            duraciones = [dur_total]

    imagen_usada = decidir_imagen_video(
        tipo="oracion",
        titulo=titulo,
        texto=texto
    )   

    fondo, grad = crear_fondo(dur_total, imagen_usada)

    crear_imagen_titulo(titulo, "titulo.png")
    titulo_clip = ImageClip("titulo.png").set_duration(dur_total).set_position(("center", 120)).set_opacity(1)

    clips = []
    t = 0
    for b, dur_b in zip(bloques, duraciones):
        crear_imagen_texto(b, "bloque.png")
        c = ImageClip("bloque.png").set_duration(dur_b).set_position("center")
        if (not modo_test) and len(bloques) > 1:
            c = c.fx(fadein, 1).set_start(t)
        clips.append(c)
        t += dur_b


    usar_tts = decidir_tts_para_video(
        porcentaje=TTS_PORCENTAJE_ORACION,
        seed=f"{texto}|{imagen_usada}|{video_id}"
    )

    if force_tts is not None:
        usar_tts = force_tts

    audio_duracion = dur_total + CTA_DUR
    audio, musica_usada = crear_audio(
        audio_duracion,
        musica_fija,
        usar_tts=usar_tts,
        texto_tts=texto
    )

    licencia_path = (
        f"musica/licence/licence_{musica_usada.replace('.mp3','')}.txt"
        if musica_usada
        else None
    )

    duracion_norm = int(round(audio_duracion))

    # Fingerprint del contenido
    fingerprint = generar_fingerprint_contenido(
        tipo="oracion",
        texto=texto,
        imagen=imagen_usada,
        musica=musica_usada,
        duracion=duracion_norm
    )

    intentos = 0
    while fingerprint_existe_ultimos_dias(fingerprint) and intentos < 5:
        print("⚠ Contenido duplicado (120 días) → cambiando música")
        #fondo, grad = crear_fondo(dur_total, None)
        audio, musica_usada = crear_audio(audio_duracion, None)
        fingerprint = generar_fingerprint_contenido(
            tipo="oracion",
            texto=texto,
            imagen=imagen_usada,
            musica=musica_usada,
            duracion=duracion_norm
        )
        intentos += 1

    componer_video(fondo, grad, titulo_clip, audio, clips, path_out)

    if os.path.exists(path_out):
        if modo_test:
            print(f"[TEST] Video generado (no persistido): {path_out}")
        else:
            try:
                insert_video({
                    "id": video_id,
                    "channel_id": 7,  # luego lo haces dinámico
                    "archivo": path_out,
                    "tipo": "oracion",
                    "musica": musica_usada,
                    "licencia": licencia_path,
                    "imagen": imagen_usada,
                    "texto_base": texto,
                    "fingerprint": fingerprint,
                    "metadata": {
                        "has_voice": usar_tts,
                        "voice_engine": "edge_tts" if usar_tts else None,
                        "experiment": "tts_oracion_v1",
                        "tts_ratio": TTS_PORCENTAJE_ORACION,
                    }
                })
            except Exception:
                # rollback del filesystem
                os.remove(path_out)
                raise
    else:
        raise RuntimeError(f"No se pudo crear el archivo final: {path_out}")

    limpiar_temporales()
