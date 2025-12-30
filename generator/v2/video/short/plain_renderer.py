# generator/v2/video/short/plain_renderer.py

from pathlib import Path
from typing import List
import os

from moviepy.editor import ImageClip

from generator.v2.video.background_renderer import render_background
from generator.v2.video.title_renderer import render_title_layer
from generator.v2.video.text_renderer import render_text_layer
from generator.v2.video.watermark_renderer import render_watermark_layer
from generator.v2.video.cta_renderer import render_cta_clip
from generator.v2.video.composer import compose_video
from generator.v2.video.composer_models import ComposerRequest

from generator.v2.audio.audio_builder import build_audio

FADE_SECONDS = 1.0


def render_short_plain(
    *,
    title: str,
    blocks: list[dict],
    output_path: str,
    image_path: str,
    audio_req,
    config,
    background_cfg,
    title_style,
    text_style,
    text_y_start: int,
    cta_image_path: str | None = None,
    watermark_path: str | None = None,
    modo_test: bool = False,
):
    """
    Renderer SHORT – modo PLAIN
    (Texto continuo + TTS continuo)
    """

    print(f"[RENDER][PLAIN] start → {os.path.basename(output_path)}")

    render_dir = Path(output_path).parent
    layers_dir = render_dir / "layers"
    layers_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------
    # 1) TEXTO (un solo bloque visual)
    # -------------------------------------------------
    if not blocks:
        raise RuntimeError("[PLAIN] No blocks to render")

    block = blocks[0]
    duration = float(block["duration"])

    text_png = layers_dir / "text.png"

    render_text_layer(
        lines=block["text"].splitlines(),
        output_path=str(text_png),
        style=text_style,
        y_start=text_y_start,
    )

    text_clip = (
        ImageClip(str(text_png))
        .set_start(0)
        .set_duration(duration)
        .fadein(FADE_SECONDS)
        .fadeout(FADE_SECONDS)
    )

    text_duration = duration
    cta_duration = float(config.cta_seconds) if cta_image_path else 0.0
    total_audio_duration = text_duration + cta_duration 

    # -------------------------------------------------
    # 2) AUDIO (TTS + música continua)
    # -------------------------------------------------
    audio_req.duration = text_duration
    audio_req.music_duration = total_audio_duration

    audio_result = build_audio(audio_req)
    audio_clip = audio_result.audio_clip

    # -------------------------------------------------
    # 3) FONDO (cubre TODO el video)
    # -------------------------------------------------
    fondo, grad = render_background(
        image_path=image_path,
        duration=total_audio_duration,
        config=background_cfg,
    )

    layers: List[ImageClip] = [fondo, grad, text_clip]

    # -------------------------------------------------
    # 4) TÍTULO (solo durante el texto)
    # -------------------------------------------------
    title_png = layers_dir / "title.png"

    render_title_layer(
        title=title,
        output_path=str(title_png),
        style=title_style,
    )

    layers.append(
        ImageClip(str(title_png)).set_duration(text_duration)
    )

    # -------------------------------------------------
    # 5) WATERMARK (solo durante el texto)
    # -------------------------------------------------
    if watermark_path and os.path.exists(watermark_path):
        wm_png = layers_dir / "watermark.png"

        render_watermark_layer(
            watermark_path=watermark_path,
            output_path=str(wm_png),
        )

        layers.append(
            ImageClip(str(wm_png)).set_duration(text_duration)
        )

    # -------------------------------------------------
    # 6) CTA (visual-only, música continúa)
    # -------------------------------------------------
    cta_layers = None

    if cta_image_path:
        fondo_cta, grad_cta = render_background(
            image_path=image_path,
            duration=cta_duration,
            config=background_cfg,
        )

        cta_clip = render_cta_clip(
            cta_image_path=cta_image_path,
            duration=cta_duration,
        )

        cta_layers = [fondo_cta, grad_cta]

        if cta_clip:
            cta_layers.append(cta_clip)

    # -------------------------------------------------
    # 7) COMPOSICIÓN FINAL
    # -------------------------------------------------
    compose_video(
        request=ComposerRequest(
            base_layers=layers,
            overlays=[],
            audio=audio_clip,
            cta_layers=cta_layers,
            output_path=output_path,
        )
    )

    print(f"[RENDER][PLAIN] done → {output_path}")
