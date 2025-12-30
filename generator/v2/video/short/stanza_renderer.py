# generator/v2/video/short/stanza_renderer.py

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


FADE_SECONDS = 0.6  # suave, sin inventar start=...


def render_short_stanza(
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
    Renderer SHORT STANZA (salmos por estrofa)

    - NO decide TTS
    - Consume bloques visuales ya con duración resuelta
    - Si audio_req.tts_blocks viene desde pipeline, no lo toca
    """

    print(f"[RENDER][STANZA] start → {os.path.basename(output_path)}")

    render_dir = Path(output_path).parent
    layers_dir = render_dir / "layers"
    layers_dir.mkdir(parents=True, exist_ok=True)

    # -----------------------------------
    # 1) Texto → clips secuenciales
    # -----------------------------------
    text_clips: List[ImageClip] = []
    current_t = 0.0

    for i, b in enumerate(blocks):
        stanza_text = b["text"]
        duration = float(b["duration"])

        text_png = layers_dir / f"text_block_{i}.png"

        render_text_layer(
            lines=stanza_text.splitlines(),
            output_path=str(text_png),
            style=text_style,
            y_start=text_y_start,
        )

        clip = (
            ImageClip(str(text_png))
            .set_start(current_t)
            .set_duration(duration)
            .fadein(FADE_SECONDS)
            .fadeout(FADE_SECONDS)
        )

        text_clips.append(clip)
        current_t += duration

    text_duration = current_t
    cta_duration = float(config.cta_seconds) if cta_image_path else 0.0
    total_audio_duration = text_duration + cta_duration

    # -----------------------------------
    # 2) Audio
    # -----------------------------------
    # IMPORTANTÍSIMO: la música NO puede cortarse en CTA.
    # Por eso SIEMPRE pedimos audio por (texto + CTA).
    audio_req.duration = total_audio_duration

    # Si es TTS por bloques, el pipeline ya armó audio_req.tts_blocks.
    # Si no hay tts_blocks, entonces debe existir tts_text si tts_enabled.
    audio_result = build_audio(audio_req)
    audio_clip = audio_result.audio_clip

    # -----------------------------------
    # 3) Fondo (solo segmento “base”: texto)
    # -----------------------------------
    # Base dura solo el texto; CTA se compone aparte con sus layers.
    fondo, grad = render_background(
        image_path=image_path,
        duration=text_duration,
        config=background_cfg,
    )

    layers: List[ImageClip] = [fondo, grad]
    layers.extend(text_clips)

    # -----------------------------------
    # 4) Título (duración: todo el segmento de texto)
    # -----------------------------------
    title_png = layers_dir / "title.png"
    render_title_layer(
        title=title,
        output_path=str(title_png),
        style=title_style,
    )
    layers.append(ImageClip(str(title_png)).set_duration(text_duration))

    # -----------------------------------
    # 5) Watermark (duración: todo el segmento de texto)
    # -----------------------------------
    if watermark_path and os.path.exists(watermark_path):
        wm_png = layers_dir / "watermark.png"
        render_watermark_layer(
            watermark_path=watermark_path,
            output_path=str(wm_png),
        )
        layers.append(ImageClip(str(wm_png)).set_duration(text_duration))

    # -----------------------------------
    # 6) CTA layers (con fondo propio)
    # -----------------------------------
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

    # -----------------------------------
    # 7) Composición final
    # -----------------------------------
    compose_video(
        request=ComposerRequest(
            base_layers=layers,
            overlays=[],
            audio=audio_clip,
            cta_layers=cta_layers,
            output_path=output_path,
        )
    )

    print(f"[RENDER][STANZA] done → {output_path}")
