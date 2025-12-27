from moviepy.editor import ImageClip
from moviepy.video.fx.fadein import fadein
import os

ANCHO = 1080
ALTO = 1920


def render_cta_clip(
    *,
    cta_image_path: str,
    duration: float,
):
    """
    Retorna un ImageClip con CTA centrado y fade-in.
    """
    if not cta_image_path or not os.path.exists(cta_image_path):
        return None

    cta = ImageClip(cta_image_path).resize(width=int(ANCHO * 0.55))
    cta = (
        cta.set_duration(duration)
           .set_opacity(0.97)
           .fx(fadein, 0.8)
    )

    cta_x = (ANCHO - cta.w) // 2
    cta_y = int(ALTO * 0.35)

    return cta.set_position((cta_x, cta_y))
