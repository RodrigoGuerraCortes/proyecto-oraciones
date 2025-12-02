# ============================================
#             GENERAR VIDEOS CATÓLICOS
# ============================================

import os
import random
import sys
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter, UnidentifiedImageError
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
from historial import cargar_historial, guardar_historial, registrar_uso

import json


MODO_TEST = False


# --------------------------------------------
# 📌 PARÁMETROS OPCIONALES --imagen= --musica=
# --------------------------------------------
def obtener_parametros_opcionales():
    imagen = None
    musica = None

    for arg in sys.argv:
        if arg.startswith("--imagen="):
            imagen = arg.split("=", 1)[1].strip()
        if arg.startswith("--musica="):
            musica = arg.split("=", 1)[1].strip()

    return imagen, musica


# --------------------------------------------
#                 CONSTANTES
# --------------------------------------------

ANCHO = 1080
ALTO = 1920

# Oraciones
ORACION_LINEAS_MAX = 10
SEGUNDOS_BLOQUE_ORACION = 25

# Salmos
MAX_ESTROFAS = 7
SEGUNDOS_ESTROFA = 16

# Marca de agua (pon aquí tu PNG)
WATERMARK_PATH = "marca_agua.png"  # asegúrate de tener este archivo




# --------------------------------------------
# REVISION DE ARCHIVOS CORRUPTOS
# --------------------------------------------
def limpiar_imagenes_corruptas():
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
                im.verify()
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

    print(f"\n[CHECK] Imágenes válidas: {buenas}")
    print(f"       Imágenes corruptas eliminadas: {malas}\n")



# --------------------------------------------
# MANEJO DE TEMPORALES
# --------------------------------------------

def limpiar_temporales():
    archivos_temp = [
        "fondo_tmp.jpg",
        "grad_tmp.png",
        "titulo.png",
        "bloque.png",
        "estrofa.png",
    ]

    for f in archivos_temp:
        if os.path.exists(f):
            try:
                os.remove(f)
                print(f"[CLEAN] Eliminado {f}")
            except:
                pass

    try:
        for f in os.listdir("videos"):
            if "TEMP_MPY" in f or f.endswith(".png") or f.endswith(".jpg"):
                path = os.path.join("videos", f)
                if not path.endswith(".mp4"):
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
    img = Image.new("RGBA", (ANCHO, 360), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSerif-Bold.ttf", 70)
    except:
        font = ImageFont.load_default()

    if "—" in titulo:
        numero, nombre = titulo.split("—", 1)
        numero = numero.strip()
        palabras = nombre.strip().split()
        mid = len(palabras) // 2
        linea1 = " ".join(palabras[:mid])
        linea2 = " ".join(palabras[mid:])
        lineas = [numero, linea1, linea2]

    else:
        lineas = titulo.split("\n")

    y = 20
    for linea in lineas:
        w, h = draw.textbbox((0, 0), linea, font=font)[2:]
        x = (ANCHO - w) // 2

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



# --------------------------------------------
#            CALCULAR DURACION
# --------------------------------------------

def calcular_duracion_bloque(lineas):
    n = len([l for l in lineas.splitlines() if l.strip()])

    if n <= 7:
        return 20
    elif n <= 12:
        return 28
    else:
        return 35



# --------------------------------------------
#             FONDO + AUDIO
# --------------------------------------------

def crear_fondo(duracion, imagen_fija=None):
    print("\n============================")
    print(" [FONDO] Generando fondo…")
    print("============================")

    imagenes = os.listdir("imagenes")
    imagenes = [i for i in imagenes if i.lower() != "vignette.png"]

    if imagen_fija:
        print(f"[FONDO] Usando imagen fija: {imagen_fija}")
        registrar_uso("imagenes", imagen_fija)
        ruta = os.path.join("imagenes", imagen_fija)
    else:
        elegida = random.choice(imagenes)
        registrar_uso("imagenes", elegida)
        ruta = os.path.join("imagenes", elegida)
        print(f"[FONDO] Imagen seleccionada: {ruta}")

    try:
        pil = Image.open(ruta)
    except Exception as e:
        print(f"[ERROR FONDO] No se pudo abrir {ruta}: {e}")
        pil = Image.new("RGB", (ANCHO, ALTO), "black")

    pil = pil.convert("RGB").resize((ANCHO, ALTO))
    pil = pil.filter(ImageFilter.GaussianBlur(6))
    pil = Image.blend(pil, Image.new("RGB", (ANCHO, ALTO), "black"), 0.24)

    try:
        vig = Image.open("imagenes/vignette.png").convert("RGB").resize((ANCHO, ALTO))
        pil = Image.blend(pil, vig, 0.22)
    except:
        pass

    pil.save("fondo_tmp.jpg")

    fondo = ImageClip("fondo_tmp.jpg").set_duration(duracion)
    fondo = fondo.resize(lambda t: 1.04 - 0.03 * (t / duracion))

    grad = Image.new("RGBA", (ANCHO, ALTO))
    d = ImageDraw.Draw(grad)
    for y in range(ALTO):
        a = int(180 * (y / ALTO))
        d.line((0, y, ANCHO, y), fill=(0, 0, 0, a))
    grad.save("grad_tmp.png")

    grad_clip = ImageClip("grad_tmp.png").set_duration(duracion)

    return fondo, grad_clip



def crear_audio(duracion, musica_fija=None):

    audios_disponibles = os.listdir("musica")

    if musica_fija:
        ruta = os.path.join("musica", musica_fija)
        print(f"[AUDIO] Usando música fija: {musica_fija}")
        registrar_uso("musicas", musica_fija)
        audio = AudioFileClip(ruta)

        if audio.duration < duracion:
            print("[AUDIO] Música corta → loop")
            return audio_loop(audio, duration=duracion)

        return audio.subclip(0, duracion)

    # random
    intentos = 0
    while intentos < 3:
        try:
            archivo = random.choice(audios_disponibles)
            registrar_uso("musicas", archivo)
            ruta = os.path.join("musica", archivo)

            print(f"[AUDIO] Intento {intentos+1}: {ruta}")

            audio = AudioFileClip(ruta)
            dur_audio = audio.duration

            if dur_audio < duracion:
                print("[AUDIO] Música corta → loop")
                audio = audio_loop(audio, duration=duracion)
            else:
                inicio = random.uniform(0, max(0, dur_audio - duracion))
                audio = audio.subclip(inicio, inicio + duracion)

            return audio

        except Exception as e:
            print(f"[AUDIO ERROR] {e}")
            intentos += 1

    print("[AUDIO] Fallback silencioso")
    return AudioFileClip(os.path.join("musica", audios_disponibles[0])).subclip(0, 1)



# --------------------------------------------
#                 VIDEO BASE
# --------------------------------------------

def crear_video_base(fondo, grad, titulo_clip, audio, clips, salida):

    capas = [fondo, grad, titulo_clip] + clips

    # marca de agua
    if os.path.exists(WATERMARK_PATH):
        try:
            wm = ImageClip(WATERMARK_PATH).resize(width=int(ANCHO * 0.22))
            wm = wm.set_duration(fondo.duration)
            wm = wm.set_opacity(0.85).fx(fadein, 0.7)

            pos_x = ANCHO - wm.w - 2
            pos_y = ALTO - wm.h - 2
            wm = wm.set_position((pos_x, pos_y))

            capas.append(wm)
        except:
            pass

    video = CompositeVideoClip(capas).set_audio(audio)

    video.write_videofile(
        salida,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
    )



# --------------------------------------------
#        DIVIDIR ORACION LARGA
# --------------------------------------------

def dividir_en_bloques(texto, max_lineas=8):
    lineas = [l for l in texto.splitlines() if l.strip()]

    bloques = []
    for i in range(0, len(lineas), max_lineas):
        bloque_lineas = lineas[i:i+max_lineas]
        bloques.append("\n".join(bloque_lineas))

    # unir Amén si queda solo
    if len(bloques) >= 2:
        ult = bloques[-1].strip().lower().rstrip(".")
        if ult in ["amen", "amén"]:
            bloques[-2] += "\nAmén"
            bloques.pop()

    return bloques



# --------------------------------------------
#                VIDEO ORACIÓN
# --------------------------------------------

def crear_video_oracion(path_in, path_out):
    img_fija, mus_fija = obtener_parametros_opcionales()

    with open(path_in, "r", encoding="utf-8") as f:
        texto = f.read()

    base = os.path.splitext(os.path.basename(path_in))[0]
    titulo = base.replace("_", " ").title()

    lineas = [l for l in texto.splitlines() if l.strip()]

    if MODO_TEST:
        bloques = [texto]
        dur_total = 2
    else:
        if len(lineas) > ORACION_LINEAS_MAX:
            bloques = dividir_en_bloques(texto, ORACION_LINEAS_MAX)
            dur_total = sum(calcular_duracion_bloque(b) for b in bloques)
        else:
            bloques = [texto]
            dur_total = calcular_duracion_bloque(texto)

    fondo, grad = crear_fondo(dur_total, img_fija)

    crear_imagen_titulo(titulo, "titulo.png")
    titulo_clip = ImageClip("titulo.png").set_duration(dur_total).set_position(("center", 120))

    clips = []
    t = 0
    for b in bloques:
        crear_imagen_texto(b, "bloque.png")
        dur_b = 2 if MODO_TEST else calcular_duracion_bloque(b)
        c = ImageClip("bloque.png").set_duration(dur_b).set_position("center")
        if not MODO_TEST and len(bloques) > 1:
            c = c.fx(fadein, 1).set_start(t)
        clips.append(c)
        t += dur_b

    audio = crear_audio(dur_total, mus_fija)

    crear_video_base(fondo, grad, titulo_clip, audio, clips, path_out)



# --------------------------------------------
#                VIDEO SALMO
# --------------------------------------------

def crear_video_salmo(path_in, path_out):
    img_fija, mus_fija = obtener_parametros_opcionales()

    with open(path_in, "r", encoding="utf-8") as f:
        texto = f.read()

    base = os.path.splitext(os.path.basename(path_in))[0]
    partes = base.split("_", 1)
    numero = partes[0]

    if len(partes) > 1:
        nombre_raw = partes[1].replace("_", " ").strip()
        nombre_raw = nombre_raw.lower().replace("salmo ", "").replace(" salmo", "")
        nombre = nombre_raw.title()
    else:
        nombre = ""

    titulo = f"{numero} — {nombre}"

    estrofas = [e.strip() for e in texto.split("\n\n") if e.strip()]
    estrofas = estrofas[:MAX_ESTROFAS]

    if MODO_TEST:
        dur_total = 2
    else:
        dur_total = len(estrofas) * SEGUNDOS_ESTROFA

    fondo, grad = crear_fondo(dur_total, img_fija)

    crear_imagen_titulo(titulo, "titulo.png")
    titulo_clip = ImageClip("titulo.png").set_duration(dur_total).set_position(("center", 120))

    clips = []
    t = 0
    for e in estrofas:
        crear_imagen_texto(e, "estrofa.png")
        dur_e = 2 if MODO_TEST else SEGUNDOS_ESTROFA
        c = ImageClip("estrofa.png").set_duration(dur_e).set_position("center")
        if not MODO_TEST:
            c = c.fx(fadein, 0.8).set_start(t)
        clips.append(c)
        t += dur_e

    audio = crear_audio(dur_total, mus_fija)

    crear_video_base(fondo, grad, titulo_clip, audio, clips, path_out)



# --------------------------------------------
#          CREAR VARIOS ALEATORIOS
# --------------------------------------------

def elegir_no_repetido(archivos, historial, dias_no_repetir=7):
    hoy = datetime.now()
    limite = hoy - timedelta(days=dias_no_repetir)

    usados = {h["nombre"] for h in historial if datetime.fromisoformat(h["fecha"]) > limite}

    disponibles = [a for a in archivos if a.replace(".txt", "") not in usados]

    if not disponibles:
        historial.clear()
        disponibles = archivos

    elegido = random.choice(disponibles)
    historial.append({"nombre": elegido.replace(".txt", ""), "fecha": hoy.isoformat()})
    return elegido



def crear_videos_del_dia(cantidad, modo):
    hist = cargar_historial()

    carpeta = "textos/salmos" if modo == "salmo" else "textos/oraciones"
    archivos = [a for a in os.listdir(carpeta) if a.endswith(".txt")]

    for _ in range(cantidad):
        elegido = elegir_no_repetido(
            archivos,
            hist["salmos"] if modo == "salmo" else hist["oraciones"],
            dias_no_repetir=7,
        )

        entrada = f"{carpeta}/{elegido}"
        base = elegido.replace(".txt", "")
        subfolder = "oraciones" if modo == "oracion" else "salmos"
        salida = f"videos/{subfolder}/{base}.mp4"

        print(f" Generando ({modo}) → {salida}")

        if modo == "salmo":
            crear_video_salmo(entrada, salida)
        else:
            crear_video_oracion(entrada, salida)

        limpiar_temporales()

    print("[DEBUG] crear_videos_del_dia(): OK (no se guarda historial aquí)")



# --------------------------------------------
#                ENTRY POINT
# --------------------------------------------

if __name__ == "__main__":
    limpiar_imagenes_corruptas()

    if "test" in sys.argv:
        MODO_TEST = True
        print("⚠ MODO TEST ACTIVADO (10s)")

    if len(sys.argv) < 2:
        print("Uso:")
        print("  python3 generar_video.py 10 oracion")
        print("  python3 generar_video.py solo textos/oraciones/salve.txt")
        print("  python3 generar_video.py solo textos/salmos/salmo_23.txt --imagen=22.png --musica=5.mp3")
        sys.exit(1)

    modo = sys.argv[1].lower()

    # -------------------------------------------
    #         GENERAR VIDEO ÚNICO
    # -------------------------------------------
    if modo == "solo":
        if len(sys.argv) < 3:
            print("ERROR: Debes indicar el archivo.")
            sys.exit(1)

        archivo = sys.argv[2]

        # Detectar tipo por carpeta
        if "/salmos/" in archivo.lower():
            tipo = "salmo"
        else:
            tipo = "oracion"

        base = os.path.splitext(os.path.basename(archivo))[0]
        sub = "oraciones" if tipo == "oracion" else "salmos"
        salida = f"videos/{sub}/{base}.mp4"

        print(f"[UNICO] Generando {tipo} → {salida}")

        if tipo == "salmo":
            crear_video_salmo(archivo, salida)
        else:
            crear_video_oracion(archivo, salida)

        limpiar_temporales()
        print("[UNICO] Listo ✓")
        sys.exit(0)

    # -------------------------------------------
    #          GENERACIÓN NORMAL
    # -------------------------------------------
    cantidad = int(sys.argv[1])
    tipo = sys.argv[2].lower()

    if tipo not in ["salmo", "oracion"]:
        print("ERROR: modo inválido.")
        sys.exit(1)

    crear_videos_del_dia(cantidad, tipo)
