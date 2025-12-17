# generator/image/cta.py
import os
from moviepy.editor import ImageClip
from moviepy.video.fx.fadein import fadein

ANCHO = 1080
ALTO = 1920

CTA_PATH = "cta/cta_final.png"


def crear_bloque_cta(duracion: float):
    """
    Retorna un clip (ImageClip) con CTA posicionado.
    Si no existe CTA_PATH, retorna None.
    """
    if not os.path.exists(CTA_PATH):
        return None

    try:
        cta = ImageClip(CTA_PATH).resize(width=int(ANCHO * 0.55))
        cta = cta.set_duration(duracion)
        cta = cta.set_opacity(0.97).fx(fadein, 0.8)

        cta_x = (ANCHO - cta.w) // 2
        cta_y = int(ALTO * 0.35)
        cta = cta.set_position((cta_x, cta_y))
        return cta
    except Exception as e:
        print(f"[CTA ERROR] {e}")
        return None
