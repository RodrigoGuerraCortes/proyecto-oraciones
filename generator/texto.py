# generator/texto.py
from PIL import Image, ImageDraw, ImageFont

ANCHO = 1080
ALTO = 1920


def medir_texto(draw, texto, font):
    bbox = draw.textbbox((0, 0), texto, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def crear_imagen_texto(texto: str, output: str):
    lineas = texto.splitlines()
    total = len([l for l in lineas if l.strip()])

    if total >= 14:
        tam = 62
        esp = 15
    elif total >= 10:
        tam = 72
        esp = 18
    else:
        tam = 82
        esp = 22

    img = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans.ttf", tam)
    except Exception:
        font = ImageFont.load_default()

    ancho_max = 980
    final = []

    for l in lineas:
        if not l.strip():
            final.append("")
            continue

        w, _ = medir_texto(draw, l, font)
        if w <= ancho_max:
            final.append(l)
        else:
            tmp = ""
            for p in l.split(" "):
                test = tmp + p + " "
                w2, _ = medir_texto(draw, test, font)
                if w2 <= ancho_max:
                    tmp = test
                else:
                    final.append(tmp)
                    tmp = p + " "
            final.append(tmp)

    _, h_linea = medir_texto(draw, "A", font)
    total_h = len(final) * (h_linea + esp)
    y = (ALTO - total_h) // 2 - 30

    for l in final:
        w, h = medir_texto(draw, l, font)
        x = (ANCHO - w) // 2

        for dx, dy in [(-4,-4),(4,-4),(-4,4),(4,4)]:
            draw.text((x+dx, y+dy), l, font=font, fill=(0, 0, 0, 255))

        draw.text(
            (x, y),
            l,
            font=font,
            fill=(255, 255, 255, 255),
            stroke_width=4,
            stroke_fill="black",
        )
        y += h + esp

    img.save(output)
