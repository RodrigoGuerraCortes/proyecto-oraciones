# generator/v3/short/generar_short_stanza_generico.py

import os
from moviepy.editor import ImageClip
from moviepy.video.fx.fadein import fadein

from generator.v3.adapter.fondo_adapter import crear_fondo_v3
from generator.v3.adapter.titulo_adapter import crear_imagen_titulo_v3
from generator.v3.adapter.texto_adapter import crear_imagen_texto_v3
from generator.v3.adapter.composer_adapter import componer_video_v3
from generator.v3.adapter.audio_fingerprint_adapter import resolver_audio_y_fingerprint_v3
from generator.v3.adapter.persistir_adapter import persistir_video_v3

from generator.image.decision import decidir_imagen_video
from generator.cleanup import limpiar_temporales


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
    modo_test: bool,
    force_tts: bool | None,
    channel_id: int,
):
    """
    Generador genérico de shorts por estrofas (stanzas).

    NO conoce dominios (salmo, poema, etc).
    TODO el comportamiento viene desde resolved_config.
    """

    # ---------------------------------------------------------
    # Leer texto
    # ---------------------------------------------------------
    with open(text_path, "r", encoding="utf-8") as f:
        texto = f.read()

    format_cfg = resolved_config["format"]
    content_cfg = format_cfg["content"]
    audio_cfg = format_cfg["audio"]
    cta_cfg = format_cfg.get("cta", {})
    layout_cfg = format_cfg.get("layout", {})

    format_code = format_cfg["code"]

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
    # Duraciones (versión base)
    # ---------------------------------------------------------
    seconds_per_block = content_cfg.get("seconds_per_block", 10)

    if modo_test:
        duraciones = [2 for _ in estrofas]
    else:
        duraciones = [seconds_per_block for _ in estrofas]

    dur_total = sum(duraciones)

    # ---------------------------------------------------------
    # Decidir imagen de fondo
    # ---------------------------------------------------------
    imagen_usada = decidir_imagen_video(
        tipo=format_code,
        titulo=os.path.basename(text_path),
        texto=texto,
    )

    fondo, grad = crear_fondo_v3(
        duracion=dur_total,
        ruta_imagen=imagen_usada,
        base_path=resolved_config["visual"]["background"]["base_path"],
    )

    # ---------------------------------------------------------
    # Título
    # ---------------------------------------------------------
    titulo = os.path.splitext(os.path.basename(text_path))[0].replace("_", " ").title()

    crear_imagen_titulo_v3(
        titulo=titulo,
        output="titulo.png",
        **layout_cfg.get("title", {}),
    )

    titulo_clip = (
        ImageClip("titulo.png")
        .set_duration(dur_total)
        .set_position(("center", layout_cfg.get("title", {}).get("y", 120)))
        .set_opacity(1)
    )

    # ---------------------------------------------------------
    # Bloques de texto (estrofas)
    # ---------------------------------------------------------
    clips = []
    t = 0

    for estrofa, dur_b in zip(estrofas, duraciones):
        crear_imagen_texto_v3(
            texto=estrofa,
            output="bloque.png",
            **layout_cfg.get("text", {}),
        )

        clip = (
            ImageClip("bloque.png")
            .set_duration(dur_b)
            .set_position("center")
            .set_start(t)
        )

        if not modo_test:
            clip = clip.fx(fadein, 1)

        clips.append(clip)
        t += dur_b

    # ---------------------------------------------------------
    # Audio + fingerprint (antes de compose)
    # ---------------------------------------------------------
    usar_tts = audio_cfg.get("tts", {}).get("enabled", False)

    if force_tts is not None:
        usar_tts = force_tts

    cta_seconds = cta_cfg.get("seconds", 0)
    audio_duracion = dur_total + cta_seconds

    audio, musica_usada, fingerprint = resolver_audio_y_fingerprint_v3(
        tipo=format_code,
        texto=texto,
        imagen_usada=imagen_usada,
        audio_duracion=audio_duracion,
        usar_tts=usar_tts,
        audio_inicial=None,
    )

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
    )

    if not os.path.exists(output_path):
        raise RuntimeError(f"No se pudo generar el video: {output_path}")

    # ---------------------------------------------------------
    # Persistencia
    # ---------------------------------------------------------
    licencia_path = (
        f"musica/licence/licence_{musica_usada.replace('.mp3','')}.txt"
        if musica_usada
        else None
    )

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

    limpiar_temporales()
