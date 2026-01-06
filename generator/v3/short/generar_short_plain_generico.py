import os
import sys
from moviepy.editor import ImageClip
from moviepy.video.fx.fadein import fadein

from generator.v3.adapter.fondo_adapter import crear_fondo_v3 #Listo en V3
from generator.v3.adapter.titulo_adapter import crear_imagen_titulo_v3 #Listo en V3
from generator.v3.adapter.texto_adapter import crear_imagen_texto_v3 #Listo en V3
from generator.v3.adapter.audio_adapter import crear_audio_v3 #Listo en V3
from generator.v3.adapter.composer_adapter import componer_video_v3 #Listo en V3
from generator.v3.adapter.tts_adapter import crear_tts_v3
from generator.v3.generator.cleanup import limpiar_temporales #Listo en V3
from generator.v3.generator.utils.calculo_bloques import dividir_en_bloques, calcular_duracion_bloque #Listo en V3
from generator.v3.generator.decision import decidir_imagen_video #Listo en V3
from generator.v3.generator.utils.voice_ab import decidir_tts_para_video #Listo en V3
from generator.v3.adapter.audio_fingerprint_adapter import resolver_audio_y_fingerprint_v3 #Listo en V3
from generator.v3.adapter.persistir_adapter import persistir_video_v3 #Listo en V3

def generar_short_plain(
    *,
    resolved_config: dict,
    text_path: str,
    output_path: str,
    video_id: str,
    modo_test: bool = False,
    force_tts: bool | None = None,
    channel_id: int,
    music_path: str,
):
    


    # ---------------------------------------------------------
    # Leer texto
    # ---------------------------------------------------------
    if not os.path.exists(text_path):
        raise FileNotFoundError(text_path)

    with open(text_path, "r", encoding="utf-8") as f:
        texto = f.read().strip()

    if not texto:
        raise ValueError("Texto vacío")

    base_name = os.path.splitext(os.path.basename(text_path))[0]
    titulo = base_name.replace("_", " ").title()

    lineas = [l for l in texto.splitlines() if l.strip()]

    # ---------------------------------------------------------
    # Content config
    # ---------------------------------------------------------
    content_cfg = resolved_config["content"]
    max_lines = content_cfg.get("max_lines")
    bg_cfg = resolved_config["visual"]["background"]
    base_path_assest = bg_cfg.get("base_path")

    # ---------------------------------------------------------
    # CTA
    # ---------------------------------------------------------
    cta_cfg = resolved_config.get("cta", {})
    cta_seconds = int(cta_cfg.get("seconds", 0)) if cta_cfg.get("enabled") else 0

    # ---------------------------------------------------------
    # Decidir  Imagen de fondo
    # ---------------------------------------------------------
    imagen_usada = decidir_imagen_video(
        tipo=resolved_config["format"]["code"],
        titulo=titulo,
        texto=texto,
        base_path_assest=base_path_assest,
    )

    # ---------------------------------------------------------
    # División en bloques
    # ---------------------------------------------------------
    if modo_test:
        bloques = [texto]
        duraciones = [2]
        dur_total = 2
    else:
        if max_lines and len(lineas) > max_lines:
            bloques = dividir_en_bloques(texto, max_lines)
            duraciones = [calcular_duracion_bloque(b) for b in bloques]
            dur_total = sum(duraciones)
        else:
            bloques = [texto]
            dur_total = calcular_duracion_bloque(texto)
            duraciones = [dur_total]

    # ---------------------------------------------------------
    # Audio / TTS decision
    # ---------------------------------------------------------
    audio_cfg = resolved_config["audio"]
    tts_cfg = audio_cfg["tts"]

    usar_tts = False
    porcentaje = tts_cfg.get("ratio")

    if len(bloques) > 1: 
        usar_tts = True
        porcentaje = 1.0

    if tts_cfg.get("enabled"):
        usar_tts = decidir_tts_para_video(
            porcentaje=porcentaje,
            seed=f"{texto}|{imagen_usada}|{video_id}",
        )
        


    # ---------------------------------------------------------
    # Bloques de texto
    # ---------------------------------------------------------
    text_cfg = resolved_config["visual"]["text"]

    clips = []
    t = 0

    for bloque, dur_b in zip(bloques, duraciones):
        #crear_imagen_texto(
        #    bloque,
        #    "bloque.png",
        #    font=text_cfg["font"],
        #    font_size=text_cfg["font_size"],
        #    line_spacing=text_cfg["line_spacing"],
        #    max_width=text_cfg["max_width"],
        #    outline_px=text_cfg.get("outline_px", 0),
        #    outline_color=text_cfg.get("outline_color"),
        #)

        crear_imagen_texto_v3(
            texto=bloque,
            output="bloque.png",
        )

        # Si se fuerza TTS, crear TTS para calcular duración
        if force_tts is not None:

            usar_tts = force_tts

            #aca deberiamos crear el tts para calcular su duracion 
            tts_audio = crear_tts_v3(
                texto=bloque,
                engine=resolved_config["audio"]["tts"].get("engine", "edge"),
            )

            print(f"[V3] Duración TTS bloque: {tts_audio.duration} segundos")

            dur_b = tts_audio.duration
        

        clip = (
            ImageClip("bloque.png")
            .set_duration(dur_b)
            .set_position(("center"))
        )

        if not modo_test and len(bloques) > 1:
            clip = clip.fx(fadein, 1).set_start(t)

        clips.append(clip)
        t += dur_b

    audio_duracion = t
    
    print(f"[V3] Duración total calculada: {audio_duracion} segundos")
    print(f"[V3] Texto dividido en {len(bloques)} bloques.")
    print(f"[V3] Duraciones bloques: {duraciones}")
    print(f"[V3] Duración dur_b: {dur_b} segundos")
    print(f"[V3] Duración t: {t} segundos")
    print(f"[V3] Texto total duración={dur_total} segundos")


    # ---------------------------------------------------------
    # Crear Imagen de fondo
    # ---------------------------------------------------------
    fondo, grad = crear_fondo_v3(
        duracion=audio_duracion,
        ruta_imagen=imagen_usada,
        base_path=bg_cfg.get("base_path"),
    )

    # ---------------------------------------------------------
    # Título
    # ---------------------------------------------------------
    title_cfg = resolved_config["visual"]["title"]

    
    #crear_imagen_titulo(
    #    titulo,
    #    "titulo.png",
    #    font=title_cfg["font"],
    #    font_size=title_cfg["font_size"],
    #    color=title_cfg["color"],
    #    shadow=title_cfg["shadow"],
    #    max_width_chars=title_cfg.get("max_width_chars"),
    #    line_spacing=title_cfg.get("line_spacing"),
    #)

    # ---------------------------------------------------------
    # Título V3
    # -------------------------------------fcrear_fondo_v3--------------------    

    crear_imagen_titulo_v3(
        titulo=titulo,
        output=base_path_assest + "/tmp/titulo.png",
    )

    titulo_clip = (
        ImageClip(base_path_assest + "/tmp/titulo.png")
        .set_duration(audio_duracion)
        .set_position(("center", title_cfg.get("y", 120)))
    )

   
    #sys.exit()

    #audio, musica_usada = crear_audio(
    #    audio_duracion,
    #    musica_fija=None,
    #    usar_tts=usar_tts,
    #    texto_tts=texto,
    #    music_base_path=audio_cfg["music"].get("base_path"),
    #    music_strategy=audio_cfg["music"].get("strategy"),
    #    music_enabled=audio_cfg["music"].get("enabled", True),
    #    tts_engine=tts_cfg.get("engine"),
    #    tts_mode=tts_cfg.get("mode"),
    #    pause_after_title=tts_cfg.get("pause_after_title", 0.0),
    #    pause_between_blocks=tts_cfg.get("pause_between_blocks", 0.0),
    #)

    duracion_norm = int(round(audio_duracion) + cta_seconds)

    audio, musica_usada = crear_audio_v3(
        duracion=duracion_norm,
        usar_tts=usar_tts,
        texto_tts=texto,
        music_path=music_path,
    )
    #sys.exit()

    audio, musica_usada, fingerprint = resolver_audio_y_fingerprint_v3(
        tipo=resolved_config["format"]["code"],
        texto=texto,
        imagen_usada=imagen_usada,
        audio_duracion=duracion_norm,
        usar_tts=usar_tts,
        audio_inicial=(audio, musica_usada),
    )

    licencia_path = (
        f"musica/licence/licence_{musica_usada.replace('.mp3','')}.txt"
        if musica_usada
        else None
    )


    # ---------------------------------------------------------
    # Composición final
    # ---------------------------------------------------------
    #componer_video(
    #    fondo=fondo,
    #    grad=grad,
    #    titulo_clip=titulo_clip,
    #    audio=audio,
    #    text_clips=clips,
    #    output_path=output_path,
    #    cta_path=cta_cfg.get("path"),
    #    cta_seconds=cta_seconds,
    #    watermark_cfg=resolved_config["visual"].get("watermark"),
    #)


    
    componer_video_v3(
        fondo=fondo,
        grad=grad,
        titulo_clip=titulo_clip,
        audio=audio,
        text_clips=clips,
        output_path=output_path,
        visual_cfg=resolved_config["visual"],
        cta_cfg=cta_cfg,
        base_path_assest=base_path_assest,
    )
#
    if not os.path.exists(output_path):
        raise RuntimeError(f"No se pudo generar el video: {output_path}")
#
    # ---------------------------------------------------------
    # Persistencia
    # ---------------------------------------------------------
    print("[V3] Persistiendo video... Formato:", resolved_config["format"]["code"])
    
    persistir_video_v3(
        video_id=video_id,
        channel_id=channel_id,
        tipo=resolved_config["format"]["code"],
        output_path=output_path,
        texto=texto,
        imagen_usada=imagen_usada,
        musica_usada=musica_usada,
        fingerprint=fingerprint,
        usar_tts=usar_tts,
        modo_test=modo_test,
        licencia_path=licencia_path,
    )

    limpiar_temporales(base_path_assest)
