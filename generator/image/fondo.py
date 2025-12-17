# generator/image/fondo.py
import os
from PIL import Image, ImageDraw, ImageFilter
from moviepy.editor import ImageClip

ANCHO = 1080
ALTO = 1920


def crear_fondo(duracion: float, ruta_imagen: str):
    """
    ruta_imagen: ej 'jesus/30.png'
    """

    print(f"[FONDO] Renderizando fondo con {ruta_imagen}")

    ruta = os.path.join("imagenes", ruta_imagen)

    try:
        pil = Image.open(ruta)
    except Exception as e:
        raise RuntimeError(f"No se pudo abrir imagen {ruta}: {e}")

    pil = pil.convert("RGB").resize((ANCHO, ALTO))
    pil = pil.filter(ImageFilter.GaussianBlur(6))
    pil = Image.blend(
        pil,
        Image.new("RGB", (ANCHO, ALTO), "black"),
        0.14
    )

    try:
        vig = Image.open("imagenes/vignette.png").convert("RGB").resize((ANCHO, ALTO))
        pil = Image.blend(pil, vig, 0.22)
    except Exception:
        pass

    # protección anti-negro
    avg_lum = sum(pil.convert("L").resize((10, 10)).getdata()) / 100
    if avg_lum < 35:
        pil = Image.blend(
            pil,
            Image.new("RGB", (ANCHO, ALTO), "black"),
            0.08
        )

    pil.save("fondo_tmp.jpg")

    fondo = ImageClip("fondo_tmp.jpg").set_duration(duracion)

    def zoom_safe(t):
        factor = 1.04 - 0.03 * (t / duracion)
        return max(1.0, min(1.04, factor))

    fondo = fondo.resize(zoom_safe)

    # gradiente
    grad = Image.new("RGBA", (ANCHO, ALTO))
    d = ImageDraw.Draw(grad)
    for y in range(ALTO):
        a = int(100 * (y / ALTO))
        d.line((0, y, ANCHO, y), fill=(0, 0, 0, a))
    grad.save("grad_tmp.png")

    grad_clip = ImageClip("grad_tmp.png").set_duration(duracion)

    return fondo, grad_clip
