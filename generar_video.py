import os
import random
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip
from moviepy.video.fx.fadein import fadein
from datetime import datetime

ANCHO = 1080
ALTO = 1920
DURACION = 30


# ============================================================
#                  UTILIDADES DE TEXTO
# ============================================================

def medir_texto(draw, texto, font):
    bbox = draw.textbbox((0, 0), texto, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def crear_imagen_texto(texto, output_path):

    lineas_brutas = texto.splitlines()
    total_caracteres = len(texto)
    total_lineas_archivo = len([l for l in lineas_brutas if l.strip()])

    # Ajustes automáticos según largo
    if total_caracteres > 900 or total_lineas_archivo >= 14:
        tam_fuente = 62
        espacio_vertical = 16
    elif total_caracteres > 650 or total_lineas_archivo >= 10:
        tam_fuente = 72
        espacio_vertical = 18
    else:
        tam_fuente = 82
        espacio_vertical = 22

    img = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans.ttf", tam_fuente)
    except:
        font = ImageFont.load_default()

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

    # Amén: separar un poco
    if lineas_finales and lineas_finales[-1].strip().lower() == "amén":
        lineas_finales.append("")

    # Calculo centrado vertical total
    _, h_linea = medir_texto(draw, "A", font)
    total_altura = len(lineas_finales) * (h_linea + espacio_vertical)

    y = (ALTO - total_altura) // 2 - 40  # Ajuste suave hacia arriba

    for linea in lineas_finales:
        w, h = medir_texto(draw, linea, font)
        x = (ANCHO - w) // 2

        # Contorno
        for dx, dy in [
            (-4,-4),(4,-4),(-4,4),(4,4),
            (-4,0),(4,0),(0,-4),(0,4)
        ]:
            draw.text((x+dx, y+dy), linea, font=font, fill=(0,0,0,255))

        draw.text((x+2, y+2), linea, font=font, fill=(0,0,0,120))
        draw.text((x, y), linea, font=font, fill=(255,255,255,255))

        y += h + espacio_vertical

    img.save(output_path)


# ============================================================
#         GRADIENTE OSCURO DETRÁS DEL TEXTO
# ============================================================

def crear_gradiente_overlay(path):
    gradient = Image.new("RGBA", (ANCHO, ALTO))
    draw = ImageDraw.Draw(gradient)

    for y in range(ALTO):
        alpha = int(200 * (y / ALTO))
        draw.line((0, y, ANCHO, y), fill=(0, 0, 0, alpha))

    gradient.save(path)


# ============================================================
#                     CREAR VIDEO
# ============================================================
def crear_video(oracion_file, output_file):
    with open(oracion_file, "r", encoding="utf-8") as f:
        texto = f.read()

    # ---- Fondo ----
    fondo_path = os.path.join("imagenes", random.choice(os.listdir("imagenes")))
    fondo_pil = Image.open(fondo_path).convert("RGB").resize((ANCHO, ALTO))

    fondo_pil = fondo_pil.filter(ImageFilter.GaussianBlur(radius=6))
    fondo_pil = Image.blend(fondo_pil, Image.new("RGB", (ANCHO, ALTO), (0, 0, 0)), 0.22)

    fondo_tmp = "fondo_tmp.jpg"
    fondo_pil.save(fondo_tmp)

    fondo = ImageClip(fondo_tmp).set_duration(DURACION)
    fondo = fondo.resize(lambda t: 1.06 - 0.03*(t/DURACION))   # zoom lento elegante

    # ---- Texto ----
    texto_img = "textos/texto_render.png"
    crear_imagen_texto(texto, texto_img)

    texto_clip = ImageClip(texto_img).set_duration(DURACION)
    texto_clip = texto_clip.set_position("center").fx(fadein, 1.3)

    # ---- Gradiente detrás del texto ----
    grad_path = "textos/gradiente_overlay.png"
    crear_gradiente_overlay(grad_path)

    grad_clip = ImageClip(grad_path).set_duration(DURACION)
    grad_clip = grad_clip.set_position("center").fx(fadein, 1)

    # ---- AUDIO: comenzar desde el segundo 30 ----
    musica_path = os.path.join("musica", random.choice(os.listdir("musica")))
    audio = AudioFileClip(musica_path)

    INICIO_AUDIO = 5                              
    duracion_total = audio.duration

    # Evita errores: si la canción dura poco, toma los últimos 30s que existan
    inicio_real = min(INICIO_AUDIO, max(0, duracion_total - DURACION))



    # Cortamos justo desde inicio_real → inicio_real + 30s
    audio = audio.subclip(inicio_real, inicio_real + DURACION).volumex(0.32)
    audio = audio.audio_fadein(0.8).audio_fadeout(1.8)
    audio = audio.volumex(0.28)


    # sincronizado desde el segundo 0 del video
    audio = audio.set_start(0)

    # ---- COMPOSICIÓN ----
    video = CompositeVideoClip([fondo, grad_clip, texto_clip])
    video = video.set_audio(audio)

    # ---- Exportar en alta calidad ----
    video.write_videofile(
        output_file,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        preset="medium"
    )



# ============================================================
#                CREAR VARIOS VIDEOS
# ============================================================

def crear_videos_del_dia(cantidad):
    archivos = os.listdir("textos/oraciones")
    seleccion = random.sample(archivos, min(cantidad, len(archivos)))
    fecha = datetime.now().strftime("%Y%m%d")

    for i, archivo in enumerate(seleccion, start=1):
        ruta = "textos/oraciones/" + archivo
        salida = f"videos/video_{fecha}_{i}.mp4"
        print(f" Generando -> {salida}")
        crear_video(ruta, salida)


if __name__ == "__main__":
    cantidad = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    crear_videos_del_dia(cantidad)
