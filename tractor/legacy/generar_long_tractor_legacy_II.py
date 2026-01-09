
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    ImageClip,
    CompositeVideoClip,
    ColorClip,
    concatenate_videoclips,
)
import os
import textwrap
import numpy as np

from adapter.persistir_adapter import persistir_video_v3


# -------------------------------------------------
# Utilidad: renderizar texto con PIL → ImageClip
# -------------------------------------------------
def render_text_block_pil(
    *,
    text: str,
    width: int,
    height: int,
    font_path: str,
    font_size: int,
    text_color=(255, 255, 255),
    margin_x=200,
):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype(font_path, font_size)

    max_chars_per_line = 60
    lines = []

    for paragraph in text.split("\n"):
        wrapped = textwrap.wrap(paragraph, width=max_chars_per_line)
        if not wrapped:
            lines.append("")
        else:
            lines.extend(wrapped)
        lines.append("")

    line_height = font.getbbox("Ay")[3] + 12
    total_text_height = len(lines) * line_height
    y = int((height - total_text_height) / 2)

    for line in lines:
        bbox = font.getbbox(line)
        text_width = bbox[2] - bbox[0]
        x = int((width - text_width) / 2)
        draw.text((x, y), line, font=font, fill=text_color)
        y += line_height

    return ImageClip(np.array(img))


# -------------------------------------------------
# Tractor — FASE 4.2
# -------------------------------------------------
def generar_long_tractor(
    *,
    resolved_config: dict,
    output_path: str,
    video_id: str,
    channel_id: int,
    modo_test: bool = False,
    **kwargs,
):
    print("[LONG TRACTOR] FASE 4.2 — ESTRUCTURA COMPLETA (SIN TTS)")
    print("[LONG TRACTOR] Modo test:", modo_test)

    if not modo_test:
        raise RuntimeError("FASE 4.2 solo permitida en modo test")

    # -------------------------------------------------
    # Configuración base
    # -------------------------------------------------
    WIDTH = 1920
    HEIGHT = 1080

    BLOCK_DURATION = 6  # segundos por bloque (placeholder)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

    content_cfg = resolved_config["content"]
    base_path = content_cfg["base_path"]
    blocks = content_cfg["blocks"]
    repeatables = content_cfg.get("repeatable_blocks", [])
    target_minutes = content_cfg.get("target_duration_minutes", 55)

    target_seconds = target_minutes * 60

    # -------------------------------------------------
    # Leer TODOS los textos
    # -------------------------------------------------
    textos = {}
    for fname in blocks:
        path = os.path.join(base_path, fname)
        with open(path, "r", encoding="utf-8") as f:
            textos[fname] = f.read().strip()

    print("[LONG TRACTOR] Bloques cargados:")
    for k in textos:
        print(" -", k)

    # -------------------------------------------------
    # Construcción de la secuencia lógica
    # -------------------------------------------------
    timeline_blocks = []

    # 1) bloques iniciales (en orden)
    for b in blocks:
        timeline_blocks.append(b)

    # 2) repetir bloques intermedios hasta acercarse al target
    estimated_duration = 0

    def estimate_blocks_duration(block_list):
        count = 0
        for b in block_list:
            count += len(textos[b].split("\n\n"))
        return count * BLOCK_DURATION

    estimated_duration = estimate_blocks_duration(timeline_blocks)

    while estimated_duration < target_seconds and repeatables:
        for b in repeatables:
            timeline_blocks.append(b)
            estimated_duration = estimate_blocks_duration(timeline_blocks)
            if estimated_duration >= target_seconds:
                break

    print(
        f"[LONG TRACTOR] Duración estimada ~ {estimated_duration/60:.1f} min"
    )

    # -------------------------------------------------
    # Renderizar bloques uno tras otro
    # -------------------------------------------------
    fondo = ColorClip(
        size=(WIDTH, HEIGHT),
        color=(0, 0, 0)
    )

    clips = []

    for fname in timeline_blocks:
        text = textos[fname]
        sub_blocks = [b.strip() for b in text.split("\n\n") if b.strip()]

        for block_text in sub_blocks:
            txt_clip = render_text_block_pil(
                text=block_text,
                width=WIDTH,
                height=HEIGHT,
                font_path=font_path,
                font_size=56,
            ).set_duration(BLOCK_DURATION)

            clip = CompositeVideoClip(
                [fondo.set_duration(BLOCK_DURATION), txt_clip],
                size=(WIDTH, HEIGHT),
            )

            clips.append(clip)

    print(f"[LONG TRACTOR] Clips generados: {len(clips)}")

    video = concatenate_videoclips(clips, method="compose")

    # -------------------------------------------------
    # Render
    # -------------------------------------------------
    print("[LONG TRACTOR] Renderizando FASE 4.2...")
    video.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio=False,
        threads=4,
        preset="ultrafast",
    )

    # -------------------------------------------------
    # Persistencia mínima
    # -------------------------------------------------
    persistir_video_v3(
        video_id=video_id,
        channel_id=channel_id,
        tipo="long_tractor_oracion",
        output_path=output_path,
        texto=" | ".join(timeline_blocks),
        imagen_usada="BLACK",
        musica_usada=None,
        fingerprint=None,
        usar_tts=False,
        modo_test=True,
        licencia_path=None,
    )

    print("[LONG TRACTOR] FASE 4.2 OK — Estructura validada")
