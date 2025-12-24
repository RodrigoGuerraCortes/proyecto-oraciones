# generator/v2/video/background_renderer.py

from dataclasses import dataclass
from typing import Tuple

from PIL import Image, ImageDraw, ImageFilter
from moviepy.editor import ImageClip


ANCHO = 1080
ALTO = 1920


@dataclass
class BackgroundConfig:
    blur_radius: int = 6
    darken_alpha: float = 0.14
    vignette_alpha: float = 0.22
    min_luminance: int = 35
    extra_darken_alpha: float = 0.08
    zoom_start: float = 1.04
    zoom_end: float = 1.0
    gradient_alpha: int = 100


def render_background(
    *,
    image_path: str,
    duration: float,
    config: BackgroundConfig,
) -> Tuple[ImageClip, ImageClip]:
    """
    Renderiza fondo + gradiente.
    """

    pil = Image.open(image_path).convert("RGB").resize((ANCHO, ALTO))

    # Blur
    pil = pil.filter(ImageFilter.GaussianBlur(config.blur_radius))

    # Darken base
    pil = Image.blend(
        pil,
        Image.new("RGB", (ANCHO, ALTO), "black"),
        config.darken_alpha,
    )

    # Protección anti-negro
    avg_lum = sum(
        pil.convert("L").resize((10, 10)).getdata()
    ) / 100

    if avg_lum < config.min_luminance:
        pil = Image.blend(
            pil,
            Image.new("RGB", (ANCHO, ALTO), "black"),
            config.extra_darken_alpha,
        )

    pil.save("fondo_tmp.jpg")

    fondo = ImageClip("fondo_tmp.jpg").set_duration(duration)

    def zoom(t):
        factor = config.zoom_start - (
            (config.zoom_start - config.zoom_end) * (t / duration)
        )
        return max(config.zoom_end, min(config.zoom_start, factor))

    fondo = fondo.resize(zoom)

    # ---------- Gradiente ----------
    grad = Image.new("RGBA", (ANCHO, ALTO))
    d = ImageDraw.Draw(grad)

    for y in range(ALTO):
        alpha = int(config.gradient_alpha * (y / ALTO))
        d.line((0, y, ANCHO, y), fill=(0, 0, 0, alpha))

    grad.save("grad_tmp.png")
    grad_clip = ImageClip("grad_tmp.png").set_duration(duration)

    return fondo, grad_clip
