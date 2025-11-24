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

# Oraciones
ORACION_LINEAS_MAX = 12
SEGUNDOS_BLOQUE_ORACION = 10

# Salmos
MAX_ESTROFAS = 7
SEGUNDOS_ESTROFA = 8




from PIL import UnidentifiedImageError


# --------------------------------------------
# REVISION DE ARCHIVOS CORRUPTOS
# --------------------------------------------
def limpiar_imagenes_corruptas():
    """
    Revisa la carpeta 'imagenes' y elimina cualquier archivo que PIL no pueda abrir.
    Esto evita que MoviePy falle por fondos defectuosos.
    """
    carpeta = "imagenes"
    imagenes = os.listdir(carpeta)

    print("\n============================")
    print(" [CHECK] Verificando imágenes corruptas...")
    print("============================")

    buenas = 0
    malas = 0

    for img in imagenes:
        path = os.path.join(carpeta, img)

        # ignorar la vignette
        if img.lower() == "vignette.png":
            continue

        try:
            with Image.open(path) as im:
                im.verify()  # detección rápida de corrupción
            # hacer un segundo test real de carga
            with Image.open(path) as im2:
                im2.convert("RGB")
            buenas += 1

        except (UnidentifiedImageError, OSError, IOError) as e:
            print(f"[CORRUPTA] {img} → eliminado ({e})")
            try:
                os.remove(path)
                malas += 1
            except:
                print(f"[ERROR] No se pudo eliminar {img}")

    print(f"\n[CHECK] Proceso completado:")
    print(f"  ✔ Imágenes válidas: {buenas}")
    print(f"  ✘ Imágenes corruptas eliminadas: {malas}\n")

    if malas > 0:
        print("[INFO] Se recomienda agregar nuevas imágenes si la cantidad bajó demasiado.")

# --------------------------------------------
# MANEJO DE ARCHIVO TEMPORALES
# --------------------------------------------


def limpiar_temporales():
    """Elimina imágenes temporales y archivos TMP generados durante el render."""
    archivos_temp = [
        "fondo_tmp.jpg",
        "grad_tmp.png",
        "titulo.png",
        "bloque.png",
        "estrofa.png",
    ]

    # borrar archivos temporales estándar
    for f in archivos_temp:
        if os.path.exists(f):
            try:
                os.remove(f)
                print(f"[CLEAN] Eliminado {f}")
            except:
                pass

    # borrar TMP creados por moviepy dentro de /videos/
    try:
        for f in os.listdir("videos"):
            if "TEMP_MPY" in f or "temp" in f.lower() or f.endswith(".png") or f.endswith(".jpg"):
                path = os.path.join("videos", f)

                # no borrar el MP4 final
                if path.endswith(".mp4"):
                    continue

                try:
                    os.remove(path)
                    print(f"[CLEAN] Eliminado {path}")
                except:
                    pass
    except:
        pass

# --------------------------------------------
#                 UTILS TEXTO
# --------------------------------------------

def medir_texto(draw, texto, font):
    bbox = draw.textbbox((0, 0), texto, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def crear_imagen_titulo(titulo, output):
    """
    Crea una imagen de título dividida en múltiples líneas.
    Especial para salmos tipo:
    'Salmo 27 — El Señor Es Mi Luz Y Mi Salvación'
    """

    # Crear lienzo del título
    img = Image.new("RGBA", (ANCHO, 360), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSerif-Bold.ttf", 70)
    except:
        font = ImageFont.load_default()

    # -----------------------------------------------------
    # Detectar si es salmo y dividir en:
    #  1) Salmo 27
    #  2) El Señor es mi luz
    #  3) y mi salvación
    # -----------------------------------------------------
    if "—" in titulo:
        numero, nombre = titulo.split("—", 1)

        numero = numero.strip()
        palabras = nombre.strip().split()

        # Dividir el nombre en 2 líneas equilibradas
        mid = len(palabras) // 2
        linea1 = " ".join(palabras[:mid])
        linea2 = " ".join(palabras[mid:])

        lineas = [numero, linea1, linea2]

    else:
        # Caso de oraciones comunes
        lineas = titulo.split("\n")

    # -----------------------------------------------------
    # Dibujar cada línea centrada con contorno
    # -----------------------------------------------------
    y = 20
    for linea in lineas:
        w, h = draw.textbbox((0, 0), linea, font=font)[2:]
        x = (ANCHO - w) // 2

        # Contorno negro suave
        for dx, dy in [(-3,0),(3,0),(0,-3),(0,3),(-3,-3),(3,-3),(-3,3),(3,3)]:
            draw.text((x+dx, y+dy), linea, font=font, fill="black")

        draw.text((x, y), linea, font=font, fill="#e4d08a")

        y += h + 12

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
    print("\n============================")
    print(" [FONDO] Generando fondo con retry…")
    print("============================")

    imagenes = os.listdir("imagenes")
    imagenes = [i for i in imagenes if i.lower() != "vignette.png"]

    intentos = 0
    max_intentos = 3

    while intentos < max_intentos:
        intentos += 1
        print(f"\n[FONDO] Intento {intentos}/{max_intentos}")

        elegida = random.choice(imagenes)
        ruta = os.path.join("imagenes", elegida)
        print(f"[FONDO] Imagen seleccionada: {ruta}")

        # Intentar abrir la imagen
        try:
            pil = Image.open(ruta)
            print(f"[FONDO] Imagen cargada correctamente ({pil.mode}, {pil.size})")
        except Exception as e:
            print(f"[ERROR FONDO] No se pudo abrir {ruta}: {e}")
            print("[FONDO] Reintentando con otra imagen…")
            continue  # saltar a otro retry

        # Intentar procesar imagen
        try:
            pil = pil.convert("RGB").resize((ANCHO, ALTO))
            pil = pil.filter(ImageFilter.GaussianBlur(6))
            pil = Image.blend(pil, Image.new("RGB", (ANCHO, ALTO), "black"), 0.24)
            print("[FONDO] Resize y blur OK")

            # vignette
            try:
                vig = Image.open("imagenes/vignette.png").convert("RGB").resize((ANCHO, ALTO))
                pil = Image.blend(pil, vig, 0.22)
                print("[FONDO] Vignette aplicada OK")
            except Exception as e:
                print(f"[WARNING] No se aplicó vignette: {e}")

            # guardar temporal
            pil.save("fondo_tmp.jpg")
            print("[FONDO] fondo_tmp.jpg guardado correctamente")

            # Crear clip MoviePy
            fondo = ImageClip("fondo_tmp.jpg").set_duration(duracion)
            fondo = fondo.resize(lambda t: 1.04 - 0.03*(t/duracion))
            print("[FONDO] Clip MoviePy creado OK")

            # Crear gradiente
            grad = Image.new("RGBA", (ANCHO, ALTO))
            d = ImageDraw.Draw(grad)
            for y in range(ALTO):
                a = int(180 * (y / ALTO))
                d.line((0, y, ANCHO, y), fill=(0, 0, 0, a))
            grad.save("grad_tmp.png")
            print("[FONDO] grad_tmp.png creado OK")

            grad_clip = ImageClip("grad_tmp.png").set_duration(duracion)

            print("[FONDO] Fondo y gradiente listos ✓\n")
            return fondo, grad_clip

        except Exception as e:
            print(f"[ERROR FONDO] Falló procesar {ruta}: {e}")
            print("[FONDO] Reintentando con otra imagen…")

    # Si agotó todos los intentos
    print("\n[FONDO ERROR GRAVE] Ninguna imagen funcionó")
    print("[FONDO] Creando fondo negro de emergencia")

    fallback = Image.new("RGB", (ANCHO, ALTO), "black")
    fallback.save("fondo_tmp.jpg")

    fondo = ImageClip("fondo_tmp.jpg").set_duration(duracion)
    grad = Image.new("RGBA", (ANCHO, ALTO))
    grad.save("grad_tmp.png")
    grad_clip = ImageClip("grad_tmp.png").set_duration(duracion)

    return fondo, grad_clip


def crear_audio(duracion):
    """
    Carga un audio aleatorio y garantiza que:
      - nunca se lea fuera del rango
      - si un mp3 falla, prueba otro
      - reintenta hasta 3 veces
    """

    audios_disponibles = os.listdir("musica")

    intentos = 0
    while intentos < 3:
        try:
            archivo = random.choice(audios_disponibles)
            ruta = os.path.join("musica", archivo)

            print(f"[AUDIO] Intento {intentos+1}: usando {ruta}")

            audio = AudioFileClip(ruta)

            # Duración real del MP3
            dur_audio = audio.duration

            # Asegurar que el subclip nunca exceda el archivo
            if dur_audio <= duracion:
                inicio = 0
                fin = dur_audio
            else:
                inicio = random.uniform(0, max(0, dur_audio - duracion))
                fin = inicio + duracion

            # Aplicar música con fade
            audio = audio.subclip(inicio, fin).audio_fadein(1).audio_fadeout(2)
            return audio

        except Exception as e:
            print(f"[AUDIO ERROR] {e}")
            print("Reintentando con otro archivo...\n")
            intentos += 1
            continue

    # Si todo falla → usar un audio vacío
    print("[AUDIO ERROR] Todos los intentos fallaron, usando audio silencioso.")
    return AudioFileClip(os.path.join("musica", audios_disponibles[0])).subclip(0, 1)

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
#         DIVIDIR ORACIÓN LARGA EN BLOQUES
# --------------------------------------------

def dividir_en_bloques(texto, max_lineas=8):
    lineas = [l for l in texto.splitlines() if l.strip()]
    bloques = []

    for i in range(0, len(lineas), max_lineas):
        bloque = "\n".join(lineas[i:i + max_lineas])
        bloques.append(bloque)

    return bloques


# --------------------------------------------
#                VIDEO ORACION
# --------------------------------------------

def crear_video_oracion(path_in, path_out):

    with open(path_in, "r", encoding="utf-8") as f:
        texto = f.read()

    base = os.path.splitext(os.path.basename(path_in))[0]
    titulo = base.replace("_", " ").title()

    lineas_real = [l for l in texto.splitlines() if l.strip()]

    # oración larga → se divide como salmo
    if len(lineas_real) > ORACION_LINEAS_MAX:
        bloques = dividir_en_bloques(texto, max_lineas=8)
        dur_total = len(bloques) * SEGUNDOS_BLOQUE_ORACION
    else:
        bloques = [texto]
        dur_total = 30

    fondo, grad = crear_fondo(dur_total)

    # título
    img_t = "titulo.png"
    crear_imagen_titulo(titulo, img_t)
    titulo_clip = ImageClip(img_t).set_duration(dur_total).set_position(("center", 120))

    # bloques de texto
    clips = []
    t = 0
    for b in bloques:
        tmp = "bloque.png"
        crear_imagen_texto(b, tmp)
        c = ImageClip(tmp).set_duration(SEGUNDOS_BLOQUE_ORACION).set_position("center").fx(fadein, 1).set_start(t)
        clips.append(c)
        t += SEGUNDOS_BLOQUE_ORACION

    audio = crear_audio(dur_total)

    crear_video_base(fondo, grad, titulo_clip, audio, clips, path_out)


# --------------------------------------------
#                VIDEO SALMO
# --------------------------------------------

def crear_video_salmo(path_in, path_out):

    with open(path_in, "r", encoding="utf-8") as f:
        texto = f.read()

    base = os.path.splitext(os.path.basename(path_in))[0]

    partes = base.split("_", 1)
    numero = partes[0]
    if len(partes) > 1:
        nombre_raw = partes[1].replace("_", " ").strip()
        # quitar la palabra "salmo" si viene incluida en el nombre
        nombre_raw = nombre_raw.lower().replace("salmo ", "").replace(" salmo", "")
        nombre = nombre_raw.title()
    else:
        nombre = ""
    titulo = f"{numero} — {nombre}"

    estrofas = [e.strip() for e in texto.split("\n\n") if e.strip()]
    estrofas = estrofas[:MAX_ESTROFAS]

    dur_total = len(estrofas) * SEGUNDOS_ESTROFA

    fondo, grad = crear_fondo(dur_total)

    img_t = "titulo.png"
    crear_imagen_titulo(titulo, img_t)
    titulo_clip = ImageClip(img_t).set_duration(dur_total).set_position(("center", 120))

    clips = []
    t = 0
    for e in estrofas:
        tmp = "estrofa.png"
        crear_imagen_texto(e, tmp)
        c = ImageClip(tmp).set_duration(SEGUNDOS_ESTROFA).set_position("center").fx(fadein, 0.8).set_start(t)
        clips.append(c)
        t += SEGUNDOS_ESTROFA

    audio = crear_audio(dur_total)

    crear_video_base(fondo, grad, titulo_clip, audio, clips, path_out)


# --------------------------------------------
#           CREAR VARIOS VIDEOS
# --------------------------------------------

def crear_videos_del_dia(cantidad, modo):

    carpeta = "textos/salmos" if modo == "salmo" else "textos/oraciones"
    archivos = os.listdir(carpeta)
    seleccion = random.sample(archivos, min(cantidad, len(archivos)))

    fecha = datetime.now().strftime("%Y%m%d")

    for i, a in enumerate(seleccion, 1):
        entrada = f"{carpeta}/{a}"
        salida = f"videos/video_{fecha}_{i}_{modo}.mp4"
        print(f" Generando ({modo}) -> {salida}")

        if modo == "salmo":
            crear_video_salmo(entrada, salida)
        else:
            crear_video_oracion(entrada, salida)

        # limpiar basura al terminar
        limpiar_temporales()


# --------------------------------------------
#                ENTRY POINT
# --------------------------------------------

if __name__ == "__main__":
    limpiar_imagenes_corruptas()

    cantidad = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    modo = sys.argv[2].lower() if len(sys.argv) > 2 else "oracion"

    if modo not in ["salmo", "oracion"]:
        print("ERROR: modo inválido. Usa: salmo | oracion")
        sys.exit(1)

    crear_videos_del_dia(cantidad, modo)
