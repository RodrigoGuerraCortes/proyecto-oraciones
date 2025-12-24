# generator/v2/video/watermark_renderer.py

from PIL import Image

ANCHO = 1080
ALTO = 1920


def render_watermark_layer(
    *,
    watermark_path: str,
    output_path: str,
):
    """
    Renderiza la MARCA DE AGUA como una CAPA PNG COMPLETA (1080x1920).
    Anclada abajo a la derecha (V1).
    """
    base = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    wm = Image.open(watermark_path).convert("RGBA")

    w_new = int(ANCHO * 0.22)
    h_new = int(wm.height * (w_new / wm.width))
    wm = wm.resize((w_new, h_new))

    x = ANCHO - wm.width - 2
    y = ALTO - wm.height - 2

    base.paste(wm, (x, y), wm)
    base.save(output_path)
