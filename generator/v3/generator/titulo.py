# generator/v3/generator/titulo.py
import textwrap
import unicodedata
from PIL import Image, ImageDraw, ImageFont
import sys
ANCHO = 1080
from spellchecker import SpellChecker


def crear_imagen_titulo(titulo: str, output: str):
    spell = SpellChecker(language='es')

    img = Image.new("RGBA", (ANCHO, 360), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSerif-Bold.ttf", 70)
    except Exception:
        font = ImageFont.load_default()
   

    print(f"[Titulo] Título original: {titulo}")
    print(f"[Titulo] output: {output}")


    # Salmo: "Salmo 34 — ..."
    if "—" in titulo:
        numero, nombre = titulo.split("—", 1)
        numero = numero.strip()
        palabras = nombre.strip().split()
        mid = len(palabras) // 2
        for palabra in palabras[:mid]:
            print(f"Sugerencia para '{palabra}': {spell.correction(palabra)}")
            linea1 = " ".join(spell.correction(palabra))

        for palabra in palabras[:mid]:
            print(f"Sugerencia para '{palabra}': {spell.correction(palabra)}")
            linea2 = " ".join(spell.correction(palabras[mid:]))

        lineas = [numero, linea1, linea2]

        print("Lineas:", lineas)

    else:
        # Oración: wrap por caracteres
         #titulo puede ser "Oracion por la paz" spell debe adaptarse a cada palabra
        palabras = titulo.split()
        tituloNormalizado = ""
        for palabra in palabras:
            print(f"Sugerencia para '{palabra}': {spell.correction(palabra)}")
            tituloNormalizado += spell.correction(palabra) + " "

        #ahora capitalizamos la primera letra de cada palabra
        tituloNormalizado = tituloNormalizado.strip().title()
        print("Título:", tituloNormalizado)

        lineas = textwrap.wrap(tituloNormalizado, width=18)

        print("[Titulo] Lineas titulo oracion:", lineas)

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
