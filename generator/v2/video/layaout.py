# generator/v2/video/layout.py
from dataclasses import dataclass

ANCHO = 1080
ALTO = 1920


@dataclass(frozen=True)
class Zone:
    x: int
    y: int
    w: int
    h: int


@dataclass(frozen=True)
class ShortLayout:
    """
    Contrato visual (canónico) para shorts.

    - title_zone: zona superior reservada para título
    - text_zone: zona central "segura" (no usa pantalla completa)
    - watermark_zone: zona inferior (solo posicionamiento)
    """
    title_zone: Zone
    text_zone: Zone
    watermark_zone: Zone


def default_short_layout() -> ShortLayout:
    """
    Replica la intención visual de V1:
    - título arriba (alto acotado)
    - texto centrado pero dentro de una zona, no canvas completo
    - watermark abajo/derecha
    """
    title = Zone(x=0, y=40, w=ANCHO, h=360)

    # Zona central: debajo del título + margen; arriba del watermark
    text_top = title.y + title.h + 30
    text_bottom = int(ALTO * 0.86)  # deja espacio inferior “respirable” (watermark)
    text = Zone(x=0, y=text_top, w=ANCHO, h=text_bottom - text_top)

    # Zona watermark (solo referencia de “área inferior”)
    wm = Zone(x=0, y=int(ALTO * 0.82), w=ANCHO, h=ALTO - int(ALTO * 0.82))

    return ShortLayout(
        title_zone=title,
        text_zone=text,
        watermark_zone=wm,
    )
