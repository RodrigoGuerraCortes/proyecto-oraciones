# generator/v2/video/short_renderer.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List
import os

from moviepy.editor import ImageClip

from generator.v2.video.background_renderer import render_background
from generator.v2.video.title_renderer import render_title_layer, TitleStyle
from generator.v2.video.text_renderer import render_text_layer, TextStyle
from generator.v2.video.watermark_renderer import render_watermark_layer
from generator.v2.video.composer import compose_video
from generator.v2.video.composer_models import ComposerRequest
from generator.v2.content.segmentation import calcular_duracion_bloque
from generator.v2.video.cta_renderer import render_cta_clip

ANCHO = 1080
ALTO = 1920


@dataclass
class ShortRenderConfig:
    """
    Mantener este dataclass es parte del contrato del pipeline.
    """
    max_lines: int
    cta_seconds: int
    fade_seconds: float = 1.0
    enable_fade_between_blocks: bool = True


def render_short(
    *,
    parsed,
    output_path: str,
    image_path: str,
    audio_req,
    config: ShortRenderConfig,
    background_cfg,
    title_style: TitleStyle,
    text_style: TextStyle,
    text_y_start: int,
    cta_image_path: str | None = None,
    watermark_path: str | None = None,
    music_base_path: str | None = None,
    music_strategy: str | None = None,
    modo_test: bool = False,
):
    """
    Renderer V2 por capas PNG.
    """

    # -------------------------------------------------
    # 1) Directorios
    # -------------------------------------------------
    render_dir = Path(output_path).parent
    layers_dir = render_dir / "layers"
    layers_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------
    # 2) TEXTO → clips secuenciales + duración REAL
    # -------------------------------------------------
    text_clips: List[ImageClip] = []
    current_t = 0.0

    for i, block in enumerate(parsed.blocks):
        text_png = (layers_dir / f"text_block_{i}.png").resolve()

        render_text_layer(
            lines=block.text.splitlines(),
            output_path=str(text_png),
            style=text_style,
            y_start=text_y_start,
        )

        if not text_png.exists():
            raise RuntimeError(f"[RENDER ERROR] text layer not created: {text_png}")
        
        base_duration = calcular_duracion_bloque(block.text)
        duration = _adjust_duration_for_test(base_duration, modo_test)

        clip = (
            ImageClip(str(text_png))
            .set_start(current_t)
            .set_duration(duration)
        )

        if config.enable_fade_between_blocks:
            clip = clip.fadein(config.fade_seconds).fadeout(config.fade_seconds)

        text_clips.append(clip)
        current_t += duration

    # duración TOTAL del video (texto manda)
    total_visual_duration = current_t

    # -------------------------------------------------
    # 3) FONDO (depende de duración total)
    # -------------------------------------------------
    fondo, grad = render_background(
        image_path=image_path,
        duration=total_visual_duration,
        config=background_cfg,
    )

    layers: List[ImageClip] = [fondo, grad]

    # -------------------------------------------------
    # 4) TÍTULO (capa completa)
    # -------------------------------------------------
    title_png = (layers_dir / "title.png").resolve()

    render_title_layer(
        title=parsed.title,
        output_path=str(title_png),
        style=title_style,
    )

    if not title_png.exists():
        raise RuntimeError(f"[RENDER ERROR] title layer not created: {title_png}")

    layers.append(
        ImageClip(str(title_png))
        .set_duration(total_visual_duration)
    )

    # -------------------------------------------------
    # 5) WATERMARK (capa completa)
    # -------------------------------------------------
    if watermark_path and os.path.exists(watermark_path):
        wm_png = (layers_dir / "watermark.png").resolve()

        render_watermark_layer(
            watermark_path=watermark_path,
            output_path=str(wm_png),
        )

        if not wm_png.exists():
            raise RuntimeError(f"[RENDER ERROR] watermark layer not created: {wm_png}")

        layers.append(
            ImageClip(str(wm_png))
            .set_duration(total_visual_duration)
        )


    # -------------------------------------------------
    # 5.5) CTA (capa completa)
    # -------------------------------------------------
    cta_layers = None

    if cta_image_path:
        CTA_DURATION = config.cta_seconds

        fondo_cta, grad_cta = render_background(
            image_path=image_path,
            duration=CTA_DURATION,
            config=background_cfg,
        )

        cta_clip = render_cta_clip(
            cta_image_path=cta_image_path,
            duration=CTA_DURATION,
        )

        cta_layers = [fondo_cta, grad_cta]

        if cta_clip:
            cta_layers.append(cta_clip)
    

    # -------------------------------------------------
    # 6) COMPOSICIÓN FINAL
    # -------------------------------------------------
    compose_video(
        request=ComposerRequest(
            base_layers=layers + text_clips,
            overlays=[],
            audio=None,
            cta_layers=cta_layers,
            output_path=output_path,
        )
    )

    return {
        "output": output_path,
        "layers_dir": str(layers_dir),
    }



def _adjust_duration_for_test(duration: float, modo_test: bool) -> float:
    """
    Reduce duración solo en modo test para acelerar validaciones visuales.
    """
    if not modo_test:
        return duration

    # mínimo legible + fade visible
    return max(3.0, duration * 0.15)
