# generator/generar_salmo.py

import os
from moviepy.editor import ImageClip
from moviepy.video.fx.fadein import fadein
from generator.image.fondo import crear_fondo
from generator.image.titulo import crear_imagen_titulo
from generator.image.texto import crear_imagen_texto
from generator.audio.selector import crear_audio
from generator.video.composer import componer_video
from generator.content.fingerprinter import generar_fingerprint_contenido
from generator.cleanup import limpiar_temporales
from generator.utils.texto import normalizar_salmo_titulo
from generator.image.decision import decidir_imagen_video
from db.repositories.video_repo import insert_video,fingerprint_existe_ultimos_dias
import os
# Salmos
MAX_ESTROFAS = 7
SEGUNDOS_ESTROFA = 16
CTA_DUR = 5

def generar_salmo(
        *,
        video_id,
        path_in: str, 
        path_out: str, 
        imagen_fija=None, 
        musica_fija=None, 
        modo_test=False):
    with open(path_in, "r", encoding="utf-8") as f:
        texto = f.read()

    base = os.path.splitext(os.path.basename(path_in))[0]
    titulo = normalizar_salmo_titulo(base)

    estrofas = [e.strip() for e in texto.split("\n\n") if e.strip()]
    estrofas = estrofas[:MAX_ESTROFAS]

    if modo_test:
        dur_total = 2
        duraciones = [2] * len(estrofas)
    else:
        dur_total = len(estrofas) * SEGUNDOS_ESTROFA
        duraciones = [SEGUNDOS_ESTROFA] * len(estrofas)
    
    imagen_usada = decidir_imagen_video(
        tipo="salmo",
        titulo=titulo,
        texto=texto
    )   

    fondo, grad = crear_fondo(dur_total, imagen_usada)

    crear_imagen_titulo(titulo, "titulo.png")
    titulo_clip = ImageClip("titulo.png").set_duration(dur_total).set_position(("center", 120)).set_opacity(1)

    clips = []
    t = 0
    for e, dur_e in zip(estrofas, duraciones):
        e = (
            e.replace("senor", "señor")
             .replace("Senor", "Señor")
             .replace("dios", "Dios")
        )
        crear_imagen_texto(e, "estrofa.png")
        c = ImageClip("estrofa.png").set_duration(dur_e).set_position("center").set_opacity(1)
        if not modo_test:
            c = c.fx(fadein, 0.8).set_start(t)
        clips.append(c)
        t += dur_e

    audio_duracion = dur_total + CTA_DUR
    audio, musica_usada = crear_audio(audio_duracion, musica_fija)

    licencia_path = f"musica/licence/licence_{musica_usada.replace('.mp3','')}.txt"

    fingerprint = generar_fingerprint_contenido(
        tipo="salmo",
        texto=texto,
        imagen=imagen_usada,
        musica=musica_usada,
        duracion=audio_duracion
    )

    intentos = 0
    while fingerprint_existe_ultimos_dias(fingerprint) and intentos < 5:
        print("⚠ Contenido duplicado (120 días) → cambiando música")
        #fondo, grad = crear_fondo(dur_total, None)
        audio, musica_usada = crear_audio(audio_duracion, None)
        fingerprint = generar_fingerprint_contenido(
            tipo="salmo",
            texto=texto,
            imagen=imagen_usada,
            musica=musica_usada,
            duracion=audio_duracion
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
                    "tipo": "salmo",
                    "musica": musica_usada,
                    "licencia": licencia_path,
                    "imagen": imagen_usada,
                    "texto_base": texto,
                    "fingerprint": fingerprint,
                })
            except Exception:
                # rollback del filesystem
                os.remove(path_out)
                raise
    else:
        raise RuntimeError(f"No se pudo crear el archivo final: {path_out}")

    limpiar_temporales()