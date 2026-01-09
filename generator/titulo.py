# generator/titulo.py
import textwrap
from PIL import Image, ImageDraw, ImageFont
from normalizacion.es import normalize_spanish

ANCHO = 1080


def crear_imagen_titulo(titulo: str, output: str):
    img = Image.new("RGBA", (ANCHO, 360), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSerif-Bold.ttf", 70)
    except Exception:
        font = ImageFont.load_default()

    print(f"[Titulo] Título original: {titulo}")
    print(f"[Titulo] output: {output}")

    # -------------------------------------------------
    # Normalización segura ES
    # -------------------------------------------------
    titulo_normalizado = normalize_spanish(titulo)
    print(f"[Titulo] Título normalizado: {titulo_normalizado}")

    # -------------------------------------------------
    # Wrapping
    # -------------------------------------------------
    lineas = textwrap.wrap(titulo_normalizado, width=18)
    print("[Titulo] Lineas titulo:", lineas)


    # -------------------------------------------------
    # Render
    # -------------------------------------------------
    y = 20
    for linea in lineas:
        bbox = draw.textbbox((0, 0), linea, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = (ANCHO - w) // 2

        # Sombra
        for dx, dy in [
            (-3, 0), (3, 0), (0, -3), (0, 3),
            (-3, -3), (3, -3), (-3, 3), (3, 3)
        ]:
            draw.text((x + dx, y + dy), linea, font=font, fill="black")

        draw.text((x, y), linea, font=font, fill="#e4d08a")
        y += h + 12

    img.save(output)
