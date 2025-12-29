# ge

from __future__ import annotations

from moviepy.editor import ImageClip

from generator.v2.video.background_renderer import render_background
from generator.v2.video.title_renderer import render_title_layer
from generator.v2.video.text_renderer import render_text_layer
from generator.v2.video.watermark_renderer import render_watermark_layer
from generator.v2.video.cta_renderer import render_cta_clip
from generator.v2.video.composer import compose_video
from generator.v2.video.composer_models import ComposerRequest
from generator.v2.audio.audio_builder import build_audio


def render_short_plain(
    *,
    output_path: str,
    fps: int,
    background_cfg,
    title_cfg,
    text_cfg,
    watermark_cfg,
    cta_cfg,
    layout_result,
    audio_req,
):
    """
    Short PLAIN renderer
    - Soporta múltiples bloques secuenciales
    - CTA entra al final
    """

    blocks = layout_result.blocks
    if not blocks:
        raise RuntimeError("[PLAIN] No blocks to render")

    # -------------------------------------------------
    # 1) Fondo base (duración total = texto + CTA)
    # -------------------------------------------------
    text_duration = sum(float(b["duration"]) for b in blocks)
    cta_duration = cta_cfg.seconds if cta_cfg else 0.0
    total_duration = text_duration + cta_duration

    print(
        "[PLAIN] "
        f"blocks={len(blocks)} | "
        f"text_duration={text_duration:.2f}s | "
        f"cta_duration={cta_duration:.2f}s | "
        f"total={total_duration:.2f}s"
    )

    base_clip = render_background(
        background_cfg,
        duration=total_duration,
    )

    base_layers = [base_clip]

    # -------------------------------------------------
    # 2) Texto (bloques secuenciales)
    # -------------------------------------------------
    overlays = []
    t = 0.0

    for i, block in enumerate(blocks):
        block_text = block["text"]
        block_duration = float(block["duration"])

        print(
            "[PLAIN-BLOCK] "
            f"idx={i} | "
            f"start={t:.2f}s | "
            f"duration={block_duration:.2f}s | "
            f"lines={block_text.count(chr(10)) + 1}"
        )

        text_clip = render_text_layer(
            text=block_text,
            style=text_cfg,
            duration=block_duration,
        )

        text_clip = text_clip.set_start(t)
        overlays.append(text_clip)

        t += block_duration

    # -------------------------------------------------
    # 3) Título
    # -------------------------------------------------
    if title_cfg:
        title_clip = render_title_layer(
            title_cfg.text,
            style=title_cfg.style,
        ).set_start(0)

        overlays.append(title_clip)

    # -------------------------------------------------
    # 4) Watermark
    # -------------------------------------------------
    if watermark_cfg:
        watermark_clip = render_watermark_layer(
            watermark_cfg,
            duration=total_duration,
        )
        overlays.append(watermark_clip)

    # -------------------------------------------------
    # 5) CTA (solo visual, sin audio)
    # -------------------------------------------------
    cta_layers = []
    if cta_cfg:
        cta_clip = render_cta_clip(
            cta_image_path=cta_cfg.image_path,
            duration=cta_duration,
        )
        cta_layers.append(cta_clip)

    # -------------------------------------------------
    # 6) Audio
    # -------------------------------------------------
    audio_req.duration = text_duration
    audio_req.music_duration = total_duration

    audio_result = build_audio(audio_req)

    # -------------------------------------------------
    # 7) Composición final
    # -------------------------------------------------
    compose_video(
        request=ComposerRequest(
            base_layers=base_layers,
            overlays=overlays,
            cta_layers=cta_layers,
            audio=audio_result.audio_clip,
            output_path=output_path,
            fps=fps,
        )
    )
