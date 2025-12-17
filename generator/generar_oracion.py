# generator/generar_oracion.py

import os
from moviepy.editor import ImageClip
from moviepy.video.fx.fadein import fadein
from generator.image.fondo import crear_fondo
from generator.image.titulo import crear_imagen_titulo
from generator.image.texto import crear_imagen_texto
from generator.audio.selector import crear_audio
from generator.video.composer import componer_video
from generator.content.tag import generar_tag_inteligente
from historial import registrar_video_generado, tag_ya_existe
from generator.scheduling.slot_resolver import programar_publicacion_exacta
from generator.cleanup import limpiar_temporales
from generator.utils.texto import dividir_en_bloques, calcular_duracion_bloque
from generator.image.decision import decidir_imagen_video

ORACION_LINEAS_MAX = 10
CTA_DUR = 5

def generar_oracion(path_in: str, path_out: str, imagen_fija=None, musica_fija=None, modo_test=False):
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

    audio_duracion = dur_total + CTA_DUR
    audio, musica_usada = crear_audio(audio_duracion, musica_fija)

    licencia_path = f"musica/licence/licence_{musica_usada.replace('.mp3','')}.txt"

    # Tag
    tag_nuevo = generar_tag_inteligente(
        tipo="oracion",
        texto=texto,
        imagen=imagen_usada,
        musica=musica_usada,
        duracion=audio_duracion
    )

    intentos = 0
    while tag_ya_existe(tag_nuevo) and intentos < 5:
        print("⚠ TAG duplicado → regenerando música e imagen...")
        #fondo, grad = crear_fondo(dur_total, None)
        audio, musica_usada = crear_audio(audio_duracion, None)
        tag_nuevo = generar_tag_inteligente(
            tipo="oracion",
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
            registrar_video_generado(
                archivo_video=path_out,
                tipo="oracion",  # o salmo
                musica=musica_usada,
                licencia=licencia_path,
                imagen=imagen_usada,
                publicar_en=programar_publicacion_exacta("oracion"),
                tag=tag_nuevo
            )
    else:
        raise RuntimeError(f"No se pudo crear el archivo final: {path_out}")

    limpiar_temporales()
