# short/generar_short_stanza_generico.py

import os
import uuid
import sys
from moviepy.editor import ImageClip
from moviepy.video.fx.fadein import fadein

from adapter.fondo_adapter import crear_fondo_v3 #Listo en V3
from adapter.titulo_adapter import crear_imagen_titulo_v3 #Listo en V3
from adapter.texto_adapter import crear_imagen_texto_v3 #Listo en V3
from adapter.composer_adapter import componer_video_v3 #Listo en V3
from adapter.audio_fingerprint_adapter import resolver_audio_y_fingerprint_v3 #Listo en V3
from adapter.persistir_adapter import persistir_video_v3 #Listo en V3
from adapter.audio_adapter import crear_audio_v3 #Listo en V3

from generator.decision import decidir_imagen_video #Listo en V3
from generator.cleanup import limpiar_temporales #Listo en V3

from generator.audio.tts_edge import generar_voz_edge #Listo en V3
from generator.audio.silence import generar_silencio #Listo en V3

#from generator.audio.tts_edge import generar_voz_edge
#from generator.audio.silence import generar_silencio


from moviepy.editor import CompositeAudioClip, concatenate_audioclips



# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def parsear_estrofas(texto: str) -> list[str]:
    """
    Divide el texto en estrofas separadas por líneas en blanco.
    """
    return [e.strip() for e in texto.split("\n\n") if e.strip()]


# ---------------------------------------------------------
# Generador genérico STANZA
# ---------------------------------------------------------

def generar_short_stanza_generico(
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
    print("[GENERAR SHORT STANZA GENÉRICO]")
    """
    Generador genérico de shorts por estrofas (stanzas).

    Compatibilidad con composer V1:
      - Si hay CTA visual (composer V1), el audio debe durar lo mismo (dur_total + CTA)
      - La voz se rellena con silencio hasta audio_duracion (si aplica)
      - La música se genera con audio_duracion
    """

    # ---------------------------------------------------------
    # Leer texto
    # ---------------------------------------------------------
    if not os.path.exists(text_path):
        raise FileNotFoundError(text_path)

    with open(text_path, "r", encoding="utf-8") as f:
        texto = f.read().strip()

    if not texto:
        raise ValueError("Texto vacío")

    format_cfg = resolved_config["format"]
    content_cfg = resolved_config["content"]
    audio_cfg = resolved_config["audio"]
    cta_cfg = resolved_config.get("cta", {})
    layout_cfg = format_cfg.get("layout", {})
    bg_cfg = resolved_config["visual"]["background"]
    base_path_assest = bg_cfg.get("base_path")
    format_code = format_cfg["code"]

    print("[DEBUG][CONFIG]")
    print(" - format_cfg:", format_cfg)

    # ---------------------------------------------------------
    # Parsear estrofas
    # ---------------------------------------------------------
    estrofas = parsear_estrofas(texto)

    max_blocks = content_cfg.get("max_blocks")
    if max_blocks:
        estrofas = estrofas[:max_blocks]

    if not estrofas:
        raise ValueError("El texto no contiene estrofas válidas")

    # ---------------------------------------------------------
    # Decidir imagen de fondo
    # ---------------------------------------------------------
    imagen_usada = decidir_imagen_video(
        tipo=format_code,
        titulo=os.path.basename(text_path),
        texto=texto,
        base_path_assest=base_path_assest,
    )

    # ---------------------------------------------------------
    # Título
    # ---------------------------------------------------------
    titulo = os.path.splitext(os.path.basename(text_path))[0].replace("_", " ").title()

    crear_imagen_titulo_v3(
        titulo=titulo,
        output=base_path_assest + "/tmp/titulo.png",
        **layout_cfg.get("title", {}),
    )

    # ---------------------------------------------------------
    # Audio STANZA + TTS por bloques
    # ---------------------------------------------------------
    tts_cfg = audio_cfg.get("tts", {})
    usar_tts = bool(tts_cfg.get("enabled", False))

    if force_tts is not None:
        usar_tts = force_tts

    pause_after_title = float(tts_cfg.get("pause_after_title", 0.0))
    pause_between_blocks = float(tts_cfg.get("pause_between_blocks", 0.0))

    voces = []
    duraciones_audio = []

    if usar_tts:
        # ---------- TÍTULO HABLADO ----------
        tts_titulo_path = f"tmp/tts_titulo_{uuid.uuid4().hex}.wav"
        voz_titulo = generar_voz_edge(
            texto=titulo,
            salida_wav=tts_titulo_path
        )
        voces.append(voz_titulo)
        duraciones_audio.append(voz_titulo.duration)

        if pause_after_title > 0:
            silencio = generar_silencio(pause_after_title)
            voces.append(silencio)
            duraciones_audio.append(pause_after_title)

        # ---------- ESTROFAS HABLADAS ----------
        for idx, estrofa in enumerate(estrofas):
            tts_path = f"tmp/tts_{uuid.uuid4().hex}.wav"
            voz = generar_voz_edge(
                texto=estrofa,
                salida_wav=tts_path
            )
            voces.append(voz)
            duraciones_audio.append(voz.duration)

            if idx < len(estrofas) - 1 and pause_between_blocks > 0:
                silencio = generar_silencio(pause_between_blocks)
                voces.append(silencio)
                duraciones_audio.append(pause_between_blocks)

        voz_compuesta = concatenate_audioclips(voces)
        dur_total = float(voz_compuesta.duration)

    else:
        # ---------------------------------------------------------
        # Sin TTS: duración fija por bloque (como modo clásico)
        # ---------------------------------------------------------
        seconds_per_block = float(content_cfg.get("seconds_per_block", 10))

        if modo_test:
            duraciones = [2.0 for _ in estrofas]
        else:
            duraciones = [seconds_per_block for _ in estrofas]

        dur_total = float(sum(duraciones))
        voz_compuesta = None  # no se usa

        # construir duraciones_audio para sincronizar visuales igual
        # (una entrada por estrofa)
        duraciones_audio = duraciones[:]

    # ---------------------------------------------------------
    # CTA (compatibilidad con plain)
    # ---------------------------------------------------------
    cta_enabled = bool(cta_cfg.get("enabled", True)) if isinstance(cta_cfg, dict) else True
    cta_seconds = int(cta_cfg.get("seconds", 0)) if cta_enabled else 0

    # Contrato compat V1: audio debe incluir CTA
    audio_duracion = float(dur_total + cta_seconds)
    #audio_duracion = float(dur_total)

    # ---------------------------------------------------------
    # Título visual y clips de texto
    # ---------------------------------------------------------
    titulo_clip = (
        ImageClip(base_path_assest + "/tmp/titulo.png")
        .set_duration(dur_total)  # el título no necesita cubrir CTA
        .set_position(("center", layout_cfg.get("title", {}).get("y", 120)))
        .set_opacity(1)
    )

    clips = []

    if usar_tts:
        # timeline calculado desde duraciones_audio (título+pausas+estrofas)
        t = 0.0
        idx_audio = 0

        # avanzar por el título hablado
        t += duraciones_audio[idx_audio]
        idx_audio += 1

        # pausa después del título (si existe)
        if pause_after_title > 0:
            t += duraciones_audio[idx_audio]
            idx_audio += 1

        for _i, estrofa in enumerate(estrofas):
            dur_voz = float(duraciones_audio[idx_audio])

            crear_imagen_texto_v3(
                texto=estrofa,
                output=base_path_assest + "/tmp/bloque.png",
                **layout_cfg.get("text", {}),
            )

            clip = (
                ImageClip(base_path_assest + "/tmp/bloque.png")
                .set_duration(dur_voz)
                .set_position("center")
                .set_start(t)
            )

            if not modo_test:
                clip = clip.fx(fadein, 1)

            clips.append(clip)

            t += dur_voz
            idx_audio += 1

            # silencio entre estrofas (si existe)
            if idx_audio < len(duraciones_audio):
                t += float(duraciones_audio[idx_audio])
                idx_audio += 1

    else:
        # sin TTS: secuencia simple por estrofa con duraciones fijas
        t = 0.0
        for estrofa, dur_b in zip(estrofas, duraciones_audio):
            crear_imagen_texto_v3(
                texto=estrofa,
                output=base_path_assest + "/tmp/bloque.png",
                **layout_cfg.get("text", {}),
            )

            clip = (
                ImageClip(base_path_assest + "/tmp/bloque.png")
                .set_duration(float(dur_b))
                .set_position("center")
                .set_start(t)
            )

            if not modo_test:
                clip = clip.fx(fadein, 1)

            clips.append(clip)
            t += float(dur_b)

    # ---------------------------------------------------------
    # Fondo / gradiente (debe cubrir audio_duracion)
    # ---------------------------------------------------------
    fondo, grad = crear_fondo_v3(
        duracion=dur_total,
        ruta_imagen=imagen_usada,
        base_path=resolved_config["visual"]["background"]["base_path"],
    )

    # ---------------------------------------------------------
    # Música / Audio final (debe durar audio_duracion)
    # ---------------------------------------------------------
    musica_clip = None
    musica_usada = None


    if usar_tts:
        # Rellenar voz hasta audio_duracion (CTA incluido)
        if voz_compuesta.duration < audio_duracion:
            voz_compuesta = concatenate_audioclips([
                voz_compuesta,
                generar_silencio(audio_duracion - voz_compuesta.duration)
            ])
        else:
            voz_compuesta = voz_compuesta.subclip(0, audio_duracion)


    music_enabled = bool(audio_cfg.get("music", False))

    if music_enabled:
        musica_clip, musica_usada = crear_audio_v3(
            duracion=audio_duracion,
            usar_tts=False,
            texto_tts=None,
            music_path=music_path
        )
        musica_clip = musica_clip.volumex(0.35)


        if musica_clip:
            audio_final = CompositeAudioClip([musica_clip, voz_compuesta])
        else:
            audio_final = voz_compuesta

    else:
        # sin voz: audio final es solo música (o silencio si no hay música)
        if musica_clip:
            audio_final = musica_clip
        else:
            audio_final = generar_silencio(audio_duracion)

    # ---------------------------------------------------------
    # fingerprint + deduplicación (adapter común)
    # ---------------------------------------------------------
    duracion_norm = int(round(audio_duracion))

    audio, musica_usada, fingerprint = resolver_audio_y_fingerprint_v3(
        tipo=format_code,
        texto=texto,
        imagen_usada=imagen_usada,
        audio_duracion=duracion_norm,
        usar_tts=usar_tts,
        audio_inicial=(audio_final, musica_usada),
    )

    if usar_tts:
        audio = CompositeAudioClip([musica_clip, voz_compuesta])
    else:
        audio = musica_clip 


    print("[DEBUG] Licencia path musica_usada:", audio_cfg['music']['base_path'] + "/licence/licence_" + musica_usada.replace('.mp3','') + ".txt")

    licencia_path = ( 
        audio_cfg['music']['base_path'] + "/licence/licence_" + musica_usada.replace('.mp3','') + ".txt"
        if musica_usada
        else None
    )

    # ---------------------------------------------------------
    # Debug (logs que prueban timeline completo)
    # ---------------------------------------------------------
    last_clip_end = max((c.start + c.duration for c in clips), default=0.0)

    print("[DEBUG][DURATIONS]")
    print(" - dur_total (contenido):", dur_total)
    print(" - cta_seconds:", cta_seconds)
    print(" - audio_duracion (contenido+cta):", audio_duracion)
    print(" - fondo_duration:", fondo.duration)
    print(" - audio_final.duration (pre-fingerprint):", audio_final.duration)
    print(" - audio.duration (post-fingerprint):", audio.duration)
    print(" - titulo_duration:", titulo_clip.duration)
    print(" - duracion estrofas:", duraciones_audio)
    print(" - last_text_clip_end:", last_clip_end)

    # ---------------------------------------------------------
    # Composición final
    # ---------------------------------------------------------
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

    if not os.path.exists(output_path):
        raise RuntimeError(f"No se pudo generar el video: {output_path}")

    # ---------------------------------------------------------
    # Persistencia
    # ---------------------------------------------------------
    persistir_video_v3(
        video_id=video_id,
        channel_id=channel_id,
        tipo=format_code,
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
