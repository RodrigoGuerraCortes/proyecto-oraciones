import os
import random
import sys
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout


# ============================================================
#                      CONSTANTES
# ============================================================

ANCHO = 1080
ALTO = 1920
DURACION_ORACION = 30      # duración total de oraciones
DURACION_ESTROFA = 6       # duración por bloque de salmos


# ============================================================
#                    UTILIDADES DE TEXTO
# ============================================================

def medir_texto(draw, texto, font):
    bbox = draw.textbbox((0, 0), texto, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def crear_imagen_titulo(titulo, output_path):
    alto_titulo = 250
    img = Image.new("RGBA", (ANCHO, alto_titulo), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSerif-Bold.ttf", 85)
    except:
        font = ImageFont.load_default()

    w, h = draw.textbbox((0, 0), titulo, font=font)[2:]
    x = (ANCHO - w) // 2
    y = 40

    # contorno suave
    for dx, dy in [(-3, 0), (3, 0), (0, -3), (0, 3), (-3, -3), (3, -3), (-3, 3), (3, 3)]:
        draw.text((x + dx, y + dy), titulo, font=font, fill="black")

    draw.text((x, y), titulo, font=font, fill="#e4d08a")
    img.save(output_path)


def crear_imagen_texto(texto, output_path):
    lineas_brutas = texto.splitlines()
    total_caracteres = len(texto)
    total_lineas = len([l for l in lineas_brutas if l.strip()])

    if total_caracteres > 900 or total_lineas >= 14:
        tam_fuente = 62
        espacio = 16
    elif total_caracteres > 650 or total_lineas >= 10:
        tam_fuente = 72
        espacio = 18
    else:
        tam_fuente = 82
        espacio = 22

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

    # "Amén" separado
    if lineas_finales and lineas_finales[-1].strip().lower() == "amén":
        lineas_finales.append("")

    _, h_linea = medir_texto(draw, "A", font)
    total_altura = len(lineas_finales) * (h_linea + espacio)

    y = (ALTO - total_altura) // 2 - 40

    for linea in lineas_finales:
        w, h = medir_texto(draw, linea, font)
        x = (ANCHO - w) // 2

        # contorno
        for dx, dy in [(-4, -4), (4, -4), (-4, 4), (4, 4),
                       (-4, 0), (4, 0), (0, -4), (0, 4)]:
            draw.text((x + dx, y + dy), linea, font=font, fill=(0, 0, 0, 255))

        draw.text((x + 2, y + 2), linea, font=font, fill=(0, 0, 0, 120))
        draw.text(
            (x, y),
            linea,
            font=font,
            fill=(255, 255, 255, 255),
            stroke_width=4,
            stroke_fill="black",
        )

        y += h + espacio

    img.save(output_path)


# ============================================================
#                 FONDO + GRADIENTE + AUDIO
# ============================================================

def crear_fondo(duracion):
    """
    Crea fondo y gradiente con la DURACIÓN REAL del video.
    Esto evita que MoviePy intente renderizar 300s cuando el video dura 30.
    """
    # Imagen base
    fondo_path = os.path.join("imagenes", random.choice(os.listdir("imagenes")))
    fondo_pil = Image.open(fondo_path).convert("RGB").resize((ANCHO, ALTO))

    fondo_pil = fondo_pil.filter(ImageFilter.GaussianBlur(radius=6))
    fondo_pil = Image.blend(fondo_pil, Image.new("RGB", (ANCHO, ALTO), (0, 0, 0)), 0.22)

    # Vignette
    vignette = Image.open("imagenes/vignette.png").resize((ANCHO, ALTO)).convert("RGB")
    fondo_pil = Image.blend(fondo_pil, vignette, 0.22)

    tmp = "fondo_tmp.jpg"
    fondo_pil.save(tmp)

    fondo = ImageClip(tmp).set_duration(duracion)
    fondo = fondo.resize(lambda t: 1.06 - 0.03 * (t / duracion))  # zoom basado en duración

    # Gradiente oscuro
    grad = Image.new("RGBA", (ANCHO, ALTO))
    draw = ImageDraw.Draw(grad)

    for y in range(ALTO):
        alpha = int(200 * (y / ALTO))
        draw.line((0, y, ANCHO, y), fill=(0, 0, 0, alpha))

    grad_path = "textos/gradiente_overlay.png"
    grad.save(grad_path)

    grad_clip = ImageClip(grad_path).set_duration(duracion)

    return fondo, grad_clip


def crear_audio(duracion_objetivo=30):
    musica_path = os.path.join("musica", random.choice(os.listdir("musica")))
    audio = AudioFileClip(musica_path)

    INICIO = 5
    dur = audio.duration
    inicio_real = min(INICIO, max(0, dur - duracion_objetivo))

    audio = audio.subclip(inicio_real, inicio_real + duracion_objetivo).volumex(0.28)
    audio = audio.audio_fadein(0.8).audio_fadeout(1.8)

    return audio


# ============================================================
#                        VIDEO BASE
# ============================================================

def crear_video_base(fondo, grad_clip, titulo_clip, audio, clips, output_file):
    video = CompositeVideoClip([fondo, grad_clip, titulo_clip] + clips)
    video = video.set_audio(audio)

    video.write_videofile(
        output_file,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        preset="medium",   # si quieres aún más velocidad: "fast"
    )


# ============================================================
#                     VIDEO DE ORACIÓN
# ============================================================

def crear_video_oracion(path_in, path_out):
    with open(path_in, "r", encoding="utf-8") as f:
        texto = f.read()

    base = os.path.splitext(os.path.basename(path_in))[0]
    titulo = base.replace("_", " ").title()

    # fondo y gradiente exactamente de 30s
    fondo, grad_clip = crear_fondo(DURACION_ORACION)

    # Título
    titulo_img = "textos/titulo_render.png"
    crear_imagen_titulo(titulo, titulo_img)
    titulo_clip = (
        ImageClip(titulo_img)
        .set_duration(DURACION_ORACION)
        .set_position(("center", 160))
    )

    # Texto principal
    texto_img = "textos/texto_render.png"
    crear_imagen_texto(texto, texto_img)
    texto_clip = (
        ImageClip(texto_img)
        .set_duration(DURACION_ORACION)
        .set_position("center")
        .fx(fadein, 1.3)
    )

    # Audio 30s
    audio = crear_audio(DURACION_ORACION)

    crear_video_base(fondo, grad_clip, titulo_clip, audio, [texto_clip], path_out)


# ============================================================
#                        VIDEO DE SALMO
# ============================================================

def crear_video_salmo(path_in, path_out):
    with open(path_in, "r", encoding="utf-8") as f:
        texto = f.read()

    base = os.path.splitext(os.path.basename(path_in))[0]
    titulo = base.replace("_", " ").title()

    estrofas = [s.strip() for s in texto.split("\n\n") if s.strip()]

    # duración total del salmo (N estrofas * DURACION_ESTROFA)
    dur_total = max(DURACION_ESTROFA * len(estrofas), DURACION_ESTROFA)

    fondo, grad_clip = crear_fondo(dur_total)

    titulo_img = "textos/titulo_render.png"
    crear_imagen_titulo(titulo, titulo_img)
    titulo_clip = ImageClip(titulo_img).set_duration(dur_total).set_position(("center", 160))

    clips = []
    t = 0

    for bloque in estrofas:
        tmp = "textos/tmp_estrofa.png"
        crear_imagen_texto(bloque, tmp)

        c = (
            ImageClip(tmp)
            .set_duration(DURACION_ESTROFA)
            .set_position("center")
            .fx(fadein, 0.8)
            .set_start(t)
        )
        clips.append(c)
        t += DURACION_ESTROFA

    audio = crear_audio(duracion_objetivo=dur_total)

    crear_video_base(fondo, grad_clip, titulo_clip, audio, clips, path_out)


# ============================================================
#                 CREAR VARIOS VIDEOS
# ============================================================

def crear_videos_del_dia(cantidad, modo):
    carpeta = "textos/salmos" if modo == "salmo" else "textos/oraciones"

    archivos = os.listdir(carpeta)
    seleccion = random.sample(archivos, min(cantidad, len(archivos)))

    fecha = datetime.now().strftime("%Y%m%d")

    for i, archivo in enumerate(seleccion, start=1):
        path_in = f"{carpeta}/{archivo}"
        path_out = f"videos/video_{fecha}_{i}_{modo}.mp4"

        print(f" Generando ({modo}) -> {path_out}")

        if modo == "salmo":
            crear_video_salmo(path_in, path_out)
        else:
            crear_video_oracion(path_in, path_out)


# ============================================================
#                       ENTRY POINT
# ============================================================

if __name__ == "__main__":
    cantidad = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    modo = sys.argv[2].lower() if len(sys.argv) > 2 else "oracion"

    if modo not in ["salmo", "oracion"]:
        print("❌ Modo inválido. Usa: salmo | oracion")
        sys.exit(1)

    crear_videos_del_dia(cantidad, modo)
