# generator/v3/generator/titulo.py
import textwrap
from PIL import Image, ImageDraw, ImageFont

ANCHO = 1080


def crear_imagen_titulo(titulo: str, output: str):
    img = Image.new("RGBA", (ANCHO, 360), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSerif-Bold.ttf", 70)
    except Exception:
        font = ImageFont.load_default()

    # Salmo: "Salmo 34 — ..."
    if "—" in titulo:
        numero, nombre = titulo.split("—", 1)
        numero = numero.strip()
        palabras = nombre.strip().split()
        mid = len(palabras) // 2
        linea1 = " ".join(palabras[:mid])
        linea2 = " ".join(palabras[mid:])
        lineas = [numero, linea1, linea2]
    else:
        # Oración: wrap por caracteres
        lineas = textwrap.wrap(titulo, width=18)

    y = 20
    for linea in lineas:
        bbox = draw.textbbox((0, 0), linea, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = (ANCHO - w) // 2

        # Sombra
        for dx, dy in [(-3,0),(3,0),(0,-3),(0,3),(-3,-3),(3,-3),(-3,3),(3,3)]:
            draw.text((x+dx, y+dy), linea, font=font, fill="black")

        draw.text((x, y), linea, font=font, fill="#e4d08a")
        y += h + 12

    img.save(output)
