# ============================================
#             GENERAR VIDEOS CATÓLICOS
# ============================================

import os
import random
import sys
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout


# --------------------------------------------
#                 CONSTANTES
# --------------------------------------------

ANCHO = 1080
ALTO = 1920

DURACION_ORACION = 30

# para salmos
MAX_ESTROFAS = 7
SEGUNDOS_ESTROFA = 8   # recomendado


# --------------------------------------------
#                 UTILS TEXTO
# --------------------------------------------

def medir_texto(draw, texto, font):
    bbox = draw.textbbox((0, 0), texto, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def crear_imagen_titulo(titulo, output):
    alto = 240
    img = Image.new("RGBA", (ANCHO, alto), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSerif-Bold.ttf", 85)
    except:
        font = ImageFont.load_default()

    w, h = medir_texto(draw, titulo, font)
    x = (ANCHO - w) // 2
    y = 30

    # contorno
    for dx, dy in [(-3,0),(3,0),(0,-3),(0,3),(-3,-3),(3,-3),(-3,3),(3,3)]:
        draw.text((x+dx, y+dy), titulo, font=font, fill="black")

    draw.text((x, y), titulo, font=font, fill="#e4d08a")
    img.save(output)


def crear_imagen_texto(texto, output):
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
    except:
        font = ImageFont.load_default()

    ancho_max = 980
    final = []

    for l in lineas:
        if not l.strip():
            final.append("")
            continue

        w,_ = medir_texto(draw, l, font)
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

    if final and final[-1].strip().lower() == "amén":
        final.append("")

    _, h_linea = medir_texto(draw, "A", font)
    total_h = len(final) * (h_linea + esp)
    y = (ALTO - total_h) // 2 + 80

    for l in final:
        w,h = medir_texto(draw, l, font)
        x = (ANCHO - w) // 2

        for dx,dy in [(-4,-4),(4,-4),(-4,4),(4,4)]:
            draw.text((x+dx,y+dy), l, font=font, fill=(0,0,0,255))

        draw.text((x, y), l, font=font, fill=(255,255,255,255), stroke_width=4, stroke_fill="black")
        y += h + esp

    img.save(output)


# --------------------------------------------
#             FONDO + AUDIO
# --------------------------------------------

def crear_fondo(duracion):
    fondo_path = os.path.join("imagenes", random.choice(os.listdir("imagenes")))
    pil = Image.open(fondo_path).convert("RGB").resize((ANCHO, ALTO))

    pil = pil.filter(ImageFilter.GaussianBlur(6))
    pil = Image.blend(pil, Image.new("RGB", (ANCHO, ALTO), "black"), 0.24)

    vig = Image.open("imagenes/vignette.png").convert("RGB").resize((ANCHO, ALTO))
    pil = Image.blend(pil, vig, 0.22)

    tmp = "fondo_tmp.jpg"
    pil.save(tmp)

    fondo = ImageClip(tmp).set_duration(duracion)
    fondo = fondo.resize(lambda t: 1.04 - 0.03*(t/duracion))

    # gradiente
    grad = Image.new("RGBA", (ANCHO, ALTO))
    d = ImageDraw.Draw(grad)
    for y in range(ALTO):
        a = int(180*(y/ALTO))
        d.line((0,y,ANCHO,y), fill=(0,0,0,a))
    grad_p = "grad_tmp.png"
    grad.save(grad_p)

    grad_clip = ImageClip(grad_p).set_duration(duracion)

    return fondo, grad_clip


def crear_audio(duracion):
    musica = os.path.join("musica", random.choice(os.listdir("musica")))
    audio = AudioFileClip(musica)
    inicio = 8
    real = min(inicio, max(0, audio.duration - duracion))
    audio = audio.subclip(real, real + duracion).audio_fadein(1).audio_fadeout(2)
    return audio


# --------------------------------------------
#                 VIDEO BASE
# --------------------------------------------

def crear_video_base(fondo, grad, titulo_clip, audio, clips, salida):
    video = CompositeVideoClip([fondo, grad, titulo_clip] + clips)
    video = video.set_audio(audio)
    video.write_videofile(
        salida,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
    )


# --------------------------------------------
#                VIDEO ORACION
# --------------------------------------------

def crear_video_oracion(path_in, path_out):

    with open(path_in, "r", encoding="utf-8") as f:
        texto = f.read()

    base = os.path.splitext(os.path.basename(path_in))[0]
    titulo = base.replace("_", " ").title()

    fondo, grad = crear_fondo(DURACION_ORACION)

    # título
    img_t = "titulo.png"
    crear_imagen_titulo(titulo, img_t)
    titulo_clip = ImageClip(img_t).set_duration(DURACION_ORACION).set_position(("center", 120))

    # texto
    img_x = "texto.png"
    crear_imagen_texto(texto, img_x)
    texto_clip = ImageClip(img_x).set_duration(DURACION_ORACION).set_position("center").fx(fadein,1)

    audio = crear_audio(DURACION_ORACION)

    crear_video_base(fondo, grad, titulo_clip, audio, [texto_clip], path_out)


# --------------------------------------------
#                VIDEO SALMO
# --------------------------------------------

def crear_video_salmo(path_in, path_out):

    with open(path_in, "r", encoding="utf-8") as f:
        texto = f.read()

    base = os.path.splitext(os.path.basename(path_in))[0]

    # ------- formateo bonito -------
    # ejemplo: "121_el_senor_es_mi_guardian"
    partes = base.split("_", 1)
    numero = partes[0]
    nombre = partes[1].replace("_"," ").title() if len(partes)>1 else ""
    titulo = f"Salmo {numero} — {nombre}"

    estrofas = [e.strip() for e in texto.split("\n\n") if e.strip()]
    estrofas = estrofas[:MAX_ESTROFAS]

    dur_total = len(estrofas) * SEGUNDOS_ESTROFA

    fondo, grad = crear_fondo(dur_total)

    # titulo
    img_t = "titulo.png"
    crear_imagen_titulo(titulo, img_t)
    titulo_clip = ImageClip(img_t).set_duration(dur_total).set_position(("center", 120))

    # estrofas
    clips = []
    t = 0
    for e in estrofas:
        tmp = "estrofa.png"
        crear_imagen_texto(e, tmp)
        c = ImageClip(tmp).set_duration(SEGUNDOS_ESTROFA).set_position("center").fx(fadein,0.8).set_start(t)
        clips.append(c)
        t += SEGUNDOS_ESTROFA

    audio = crear_audio(dur_total)

    crear_video_base(fondo, grad, titulo_clip, audio, clips, path_out)



# --------------------------------------------
#           CREAR VARIOS VIDEOS
# --------------------------------------------

def crear_videos_del_dia(cantidad, modo):

    carpeta = "textos/salmos" if modo=="salmo" else "textos/oraciones"
    archivos = os.listdir(carpeta)
    seleccion = random.sample(archivos, min(cantidad, len(archivos)))

    fecha = datetime.now().strftime("%Y%m%d")

    for i,a in enumerate(seleccion,1):
        entrada = f"{carpeta}/{a}"
        salida = f"videos/video_{fecha}_{i}_{modo}.mp4"
        print(f" Generando ({modo}) -> {salida}")

        if modo=="salmo":
            crear_video_salmo(entrada, salida)
        else:
            crear_video_oracion(entrada, salida)



# --------------------------------------------
#                ENTRY POINT
# --------------------------------------------

if __name__ == "__main__":
    cantidad = int(sys.argv[1]) if len(sys.argv)>1 else 3
    modo = sys.argv[2].lower() if len(sys.argv)>2 else "oracion"

    if modo not in ["salmo","oracion"]:
        print("ERROR: modo inválido. Usa: salmo | oracion")
        sys.exit(1)

    crear_videos_del_dia(cantidad, modo)
