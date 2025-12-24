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

ANCHO = 1080
ALTO = 1920


@dataclass
class ShortRenderConfig:
    """
    Mantener este dataclass es parte del contrato del pipeline:
    config_resolver.py lo importa y lo construye.
    """
    max_lines: int
    cta_seconds: int
    fade_seconds: float = 1.0
    enable_fade_between_blocks: bool = False


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
    cta_image_path: str | None = None,
    watermark_path: str | None = None,
    modo_test: bool = False,
):
    """
    Renderer V2 por capas PNG (debug-friendly).
    MoviePy solo compone; PIL decide layout.
    """
    # Duración visual (por ahora simple y determinista)
    durations = [2.0] * len(parsed.blocks) if modo_test else [5.0] * len(parsed.blocks)
    total_visual_duration = sum(durations)

    # Fondo
    fondo, grad = render_background(
        image_path=image_path,
        duration=total_visual_duration,
        config=background_cfg,
    )

    layers: List[ImageClip] = [fondo, grad]

    # Carpeta layers junto al output (ordenado y fácil de borrar)
    render_dir = Path(output_path).parent
    layers_dir = render_dir / "layers"
    layers_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------
    # TÍTULO (capa completa)
    # -------------------------
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
    # -------------------------
    # TEXTO (capa completa)
    # - Para layout: solo primer bloque (plain)
    # - max_lines está disponible en config si luego quieres aplicarlo
    # -------------------------
    text_png = (layers_dir / "text.png").resolve()

    render_text_layer(
        lines=parsed.blocks[0].text.splitlines(),
        output_path=str(text_png),
        style=text_style,
    )

    if not text_png.exists():
        raise RuntimeError(f"[RENDER ERROR] text layer not created: {text_png}")

    layers.append(
        ImageClip(str(text_png))
        .set_duration(total_visual_duration)
    )
    # -------------------------
    # WATERMARK (capa completa)
    # -------------------------
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

    # -------------------------
    # Composición final
    # (audio/cta se reintroducen después de cerrar layout)
    # -------------------------
    compose_video(
        request=ComposerRequest(
            base_layers=layers,
            overlays=[],
            audio=None,
            cta_layers=None,
            output_path=output_path,
        )
    )

    return {"output": output_path, "layers_dir": str(layers_dir)}
