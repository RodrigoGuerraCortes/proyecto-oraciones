import os
from PIL import Image, ImageDraw, ImageFont

ANCHO = 1080
ALTO = 1920

# ============================
#   FUNCIONES DE TEXTO
# ============================

def medir_texto(draw, texto, font):
    bbox = draw.textbbox((0, 0), texto, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def crear_imagen_texto(texto, output_path):

    # ======== 1) DETECTAR LARGO DEL TEXTO ========
    lineas_brutas = texto.splitlines()
    total_caracteres = len(texto)
    total_lineas_archivo = len([l for l in lineas_brutas if l.strip()])

    # Reglas basadas en la cantidad de texto
    if total_caracteres > 900 or total_lineas_archivo >= 14:
        tam_fuente = 62
        espacio_vertical = 16
        ajuste_y = -40
    elif total_caracteres > 650 or total_lineas_archivo >= 10:
        tam_fuente = 72
        espacio_vertical = 18
        ajuste_y = -20
    else:
        tam_fuente = 82
        espacio_vertical = 22
        ajuste_y = +40

    # ======== 2) CREAR IMAGEN ========
    img = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans.ttf", tam_fuente)
    except:
        font = ImageFont.load_default()


    # ======== 3) PROCESAR LÍNEAS RESPETANDO SALTOS ========
    ancho_max = 980
    lineas_finales = []

    for linea in lineas_brutas:
        if not linea.strip():
            lineas_finales.append("")
            continue

        w, _ = medir_texto(draw, linea, font)

        if w <= ancho_max:
            lineas_finales.append(linea)
        else:
            palabras = linea.split(" ")
            tmp = ""
            for p in palabras:
                prueba = tmp + p + " "
                w2, _ = medir_texto(draw, prueba, font)
                if w2 <= ancho_max:
                    tmp = prueba
                else:
                    lineas_finales.append(tmp)
                    tmp = p + " "
            lineas_finales.append(tmp)

    # Amén más abajo
    if lineas_finales and lineas_finales[-1].strip().lower() == "amén":
        lineas_finales.append("")

    # ======== 4) POSICIONAR EL BLOQUE (CON OFFSET EXTRA) ========
    _, h_linea = medir_texto(draw, "A", font)
    total_altura = len(lineas_finales) * (h_linea + espacio_vertical)

    offset_extra = -100  # <<< SUBE EL TEXTO 100 px
    y = (ALTO - total_altura) // 2 + ajuste_y + offset_extra

    # ======== 5) DIBUJAR TEXTO (contorno + sombra + blanco) ========
    for linea in lineas_finales:
        w, h = medir_texto(draw, linea, font)
        x = (ANCHO - w) // 2

        # Contorno grueso
        for dx, dy in [
            (-4,-4),(4,-4),(-4,4),(4,4),
            (-4,0),(4,0),(0,-4),(0,4)
        ]:
            draw.text((x+dx, y+dy), linea, font=font, fill=(0,0,0,255))

        # Sombra suave
        draw.text((x+2, y+2), linea, font=font, fill=(0,0,0,120))

        # Texto blanco
        draw.text((x, y), linea, font=font, fill=(255,255,255,255))

        y += h + espacio_vertical

    img.save(output_path)


# ============================
#   GENERAR PREVIEWS
# ============================

def generar_previews():
    carpeta_oraciones = "textos/oraciones"
    carpeta_salida = "previews"

    os.makedirs(carpeta_salida, exist_ok=True)

    archivos = sorted(os.listdir(carpeta_oraciones))
    print(f"Generando previews para {len(archivos)} oraciones...\n")

    for i, archivo in enumerate(archivos, start=1):
        ruta = os.path.join(carpeta_oraciones, archivo)
        with open(ruta, "r", encoding="utf-8") as f:
            texto = f.read()

        salida = os.path.join(carpeta_salida, f"texto_{i}.png")
        print(f" ✔ Creado -> {salida}")
        crear_imagen_texto(texto, salida)

    print("\nFinalizado. Revisa la carpeta /previews/")

if __name__ == "__main__":
    generar_previews()
