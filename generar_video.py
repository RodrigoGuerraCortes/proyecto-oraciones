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
from historial import registrar_video_generado, tag_ya_existe, cargar_historial, guardar_historial
import textwrap
from moviepy.editor import concatenate_videoclips
import hashlib
from logic.text_seleccion import elegir_no_repetido


import json 

# FIX para compatibilidad con Pillow 10+
from PIL import Image

if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS



HORARIOS = ["11:00", "15:30", "23:10"]

HORARIOS_TIPO = [
    ("11:00", "oracion"),
    ("15:30", "salmo"),
    ("23:10", "oracion"),
]


def programar_publicacion_exacta(tipo):
    """
    Asigna el próximo slot disponible para el TIPO indicado
    respetando SIEMPRE la regla por día:

      11:00  -> oracion
      15:30  -> salmo
      23:10  -> oracion

    Busca en historial (pendientes + publicados) y no pisa horas ya usadas.
    """

    assert tipo in ["oracion", "salmo"], f"Tipo inválido: {tipo}"

    hist = cargar_historial()

    # -------------------------------
    # 1) Construir set de slots ocupados
    # -------------------------------
    ocupados = set()  # (fecha(date), "HH:MM")

    for lista in ("publicados", "pendientes"):
        for item in hist.get(lista, []):
            ts = item.get("publicar_en")
            if not ts:
                continue
            try:
                dt = datetime.fromisoformat(ts)
            except Exception:
                # Si el formato es viejo (sin publicar_en), lo ignoramos
                continue

            fecha = dt.date()
            hora = dt.strftime("%H:%M")
            ocupados.add((fecha, hora))

    # -------------------------------
    # 2) Buscar el próximo slot libre para ese tipo
    # -------------------------------
    ahora = datetime.now()
    dia = ahora.date()

    # Buscamos como máximo 365 días hacia adelante (más que suficiente)
    for _ in range(365):
        for hora_str, tipo_slot in HORARIOS_TIPO:
            if tipo_slot != tipo:
                continue

            # Fecha + hora del slot que estamos evaluando
            hh, mm = map(int, hora_str.split(":"))
            dt_slot = datetime(dia.year, dia.month, dia.day, hh, mm)

            # Solo slots estrictamente a futuro
            if dt_slot <= ahora:
                continue

            # ¿Ya está ocupado por algún video?
            if (dia, hora_str) in ocupados:
                continue

            # Encontrado: devolvemos en formato ISO con -03:00
            return dt_slot.strftime("%Y-%m-%dT%H:%M:%S-03:00")

        # Pasamos al día siguiente
        from datetime import timedelta
        dia = dia + timedelta(days=1)

    # -------------------------------
    # 3) Fallback (no debería pasar)
    # -------------------------------
    dt_fallback = ahora + timedelta(hours=1)
    return dt_fallback.strftime("%Y-%m-%dT%H:%M:%S-03:00")



def programar_publicacion_por_hora_actual():
    ahora = datetime.now()

    for h in HORARIOS:
        hh, mm = map(int, h.split(":"))
        dt = ahora.replace(hour=hh, minute=mm, second=0, microsecond=0)

        if dt > ahora:
            return dt.isoformat()

    # Si ya pasaron todas, usar mañana 11:00
    mañana = ahora + timedelta(days=1)
    dt = mañana.replace(hour=11, minute=0, second=0, microsecond=0)
    return dt.isoformat()


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

MODO_TEST = False
CTA_DUR = 5

# Guardará la imagen REAL usada por crear_fondo()
ultima_imagen_usada = None

CTA_PATH = "cta/cta_final.png"



def generar_tag_inteligente(tipo, texto, imagen, musica, duracion):
    # Hash del texto puro
    texto_hash = hashlib.sha256(texto.encode()).hexdigest()[:12]

    # Hash final del video según variantes reales
    contenido = f"{tipo}|{texto_hash}|{imagen}|{musica}|{duracion}"
    h = hashlib.sha256(contenido.encode()).hexdigest()

    return h[:16]


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

    # ----------------------------
    # 🔥 SI ES SALMO (contiene —)
    # ----------------------------
    if "—" in titulo:
        numero, nombre = titulo.split("—", 1)
        numero = numero.strip()
        palabras = nombre.strip().split()
        mid = len(palabras) // 2
        linea1 = " ".join(palabras[:mid])
        linea2 = " ".join(palabras[mid:])
        lineas = [numero, linea1, linea2]

    else:
        # ------------------------------------------
        # 🟦 ORACIÓN: aplicar word wrap AUTOMÁTICO
        # ------------------------------------------
        max_width = 900  # ancho máximo antes de cortar la línea
        wrapped = []

        for parte in titulo.split():
            pass
        
        # textwrap usa cantidad de caracteres, no pixeles.
        # Ajustamos por experiencia: 16–18 chars por línea
        wrapped = textwrap.wrap(titulo, width=18)

        lineas = wrapped

    # -----------------------------
    # Renderizado de líneas centrado
    # -----------------------------
    y = 20
    for linea in lineas:
        w, h = draw.textbbox((0, 0), linea, font=font)[2:]
        x = (ANCHO - w) // 2

        # Sombra suave
        for dx, dy in [(-3,0),(3,0),(0,-3),(0,3),(-3,-3),(3,-3),(-3,3),(3,3)]:
            draw.text((x+dx, y+dy), linea, font=font, fill="black")

        # Texto principal
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
    
    global ultima_imagen_usada


    if imagen_fija:
        ultima_imagen_usada = imagen_fija
        ruta = os.path.join("imagenes", imagen_fija)
        print(f"[FONDO] Usando imagen fija: {imagen_fija}")
    else:
        elegida = random.choice(imagenes)
        ultima_imagen_usada = elegida
        ruta = os.path.join("imagenes", elegida)
        print(f"[FONDO] Imagen seleccionada: {elegida}")

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

    def zoom_safe(t):
        factor = 1.04 - 0.03 * (t / duracion)
        if factor < 1.0:
            factor = 1.0
        if factor > 1.04:
            factor = 1.04
        return factor

    fondo = fondo.resize(zoom_safe) 
    #fondo = fondo.resize(lambda t: 1.04 - 0.03 * (t / duracion))

    grad = Image.new("RGBA", (ANCHO, ALTO))
    d = ImageDraw.Draw(grad)
    for y in range(ALTO):
        a = int(180 * (y / ALTO))
        d.line((0, y, ANCHO, y), fill=(0, 0, 0, a))
    grad.save("grad_tmp.png")

    grad_clip = ImageClip("grad_tmp.png").set_duration(duracion)

    return fondo, grad_clip


def audio_loop(audio, duration):
    """Repite un audio hasta completar duration."""
    loops = []
    tiempo = 0

    while tiempo < duration:
        clip = audio.subclip(0, min(audio.duration, duration - tiempo))
        loops.append(clip)
        tiempo += audio.duration

    return concatenate_videoclips(loops)


def crear_audio(duracion, musica_fija=None):
    audios_disponibles = os.listdir("musica")

    # -----------------------------------
    # 🎵 SI HAY MÚSICA FIJA (elegida con --musica=)
    # -----------------------------------
    if musica_fija:
        ruta = os.path.join("musica", musica_fija)
        print(f"[AUDIO] Usando música fija: {musica_fija}")

        audio = AudioFileClip(ruta)

        # Loop si es más corta que el video
        if audio.duration < duracion:
            print("[AUDIO] Música corta → loop automático")
            audio = audio_loop(audio, duration=duracion)
        else:
            audio = audio.subclip(0, duracion)

        return audio, musica_fija   # ⭐ SIEMPRE DEVOLVER 2 VALORES

    # -----------------------------------
    # 🎵 MÚSICA ALEATORIA
    # -----------------------------------
    intentos = 0
    while intentos < 3:
        try:
            archivo = random.choice(audios_disponibles)
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

            return audio, archivo  # ⭐ DEVOLVER 2 VALORES

        except Exception as e:
            print(f"[AUDIO ERROR] {e}")
            intentos += 1

    # -----------------------------------
    # 🎵 FALLBACK (nunca debe suceder)
    # -----------------------------------
    archivo = audios_disponibles[0]
    print("[AUDIO] Fallback silencioso")
    audio = AudioFileClip(os.path.join("musica", archivo)).subclip(0, duracion)

    return audio, archivo


# --------------------------------------------
#                 VIDEO BASE (NUEVO CTA)
# --------------------------------------------

def crear_video_base(fondo, grad, titulo_clip, audio, clips, salida):

    # --------------------
    # CAPAS PRINCIPALES
    # --------------------
    capas_principales = [fondo, grad, titulo_clip] + clips

    # Marca de agua
    if os.path.exists(WATERMARK_PATH):
        try:
            wm = ImageClip(WATERMARK_PATH).resize(width=int(ANCHO * 0.22))
            wm = wm.set_duration(fondo.duration)
            wm = wm.set_opacity(0.85).fx(fadein, 0.7)

            pos_x = ANCHO - wm.w - 2
            pos_y = ALTO - wm.h - 2
            wm = wm.set_position((pos_x, pos_y))

            capas_principales.append(wm)
        except:
            pass

    # Video principal
    video_base = CompositeVideoClip(capas_principales).set_audio(audio)

    # ===========================================
    # ⭐   BLOQUE FINAL DE CTA (5 segundos)
    # ===========================================

    DUR_FINAL = 5

    fondo_final = ImageClip("fondo_tmp.jpg").set_duration(DUR_FINAL)
    fondo_final = fondo_final.resize(lambda t: 1.04)

    grad_final = ImageClip("grad_tmp.png").set_duration(DUR_FINAL)

    capas_final = [fondo_final, grad_final]

    # CTA FINAL
    if os.path.exists(CTA_PATH):
        try:
            cta = ImageClip(CTA_PATH).resize(width=int(ANCHO * 0.55))
            cta = cta.set_duration(DUR_FINAL)
            cta = cta.set_opacity(0.97).fx(fadein, 0.8)

            # 📌 Posición perfecta: centrado 50% vertical
            cta_x = (ANCHO - cta.w) // 2
            cta_y = int(ALTO * 0.35)  # un poco más arriba del centro

            cta = cta.set_position((cta_x, cta_y))

            capas_final.append(cta)

        except Exception as e:
            print(f"[CTA ERROR] {e}")

    video_cta = CompositeVideoClip(capas_final)

    # ===========================================
    # UNIR VIDEO + BLOQUE FINAL
    # ===========================================
    final = concatenate_videoclips([video_base, video_cta])

    final.write_videofile(
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
    titulo_clip = ImageClip("titulo.png").set_duration(dur_total).set_position(("center", 120)).set_opacity(1)

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

    audio_duracion = dur_total + CTA_DUR
    audio, musica_usada = crear_audio(audio_duracion, mus_fija)

    licencia_path = f"musica/licence/licence_{musica_usada.replace('.mp3','')}.txt"

    tag_nuevo = generar_tag_inteligente(
        tipo="oracion",
        texto=texto,
        imagen=ultima_imagen_usada,
        musica=musica_usada,
        duracion=audio_duracion
    )

    # 🔥 Validación de colisión
    intentos = 0
    while tag_ya_existe(tag_nuevo) and intentos < 5:
        print("⚠ TAG duplicado → regenerando música e imagen...")
        
        # Regenerar imagen (crear_fondo actualiza ultima_imagen_usada)
        fondo, grad = crear_fondo(dur_total, None)
        imagen_regenerada = ultima_imagen_usada  # sincronización real

        # Regenerar música
        audio, musica_usada = crear_audio(audio_duracion, None)

        # Crear nuevo tag
        tag_nuevo = generar_tag_inteligente(
            tipo="oracion",
            texto=texto,
            imagen=imagen_regenerada,
            musica=musica_usada,
            duracion=audio_duracion
        )
        intentos += 1

    # 1. Renderizar primero el video
    crear_video_base(fondo, grad, titulo_clip, audio, clips, path_out)

    # 2. Verificar que el video existe realmente
    if os.path.exists(path_out):
        registrar_video_generado(
            archivo_video=path_out,
            tipo="oracion",
            musica=musica_usada,
            licencia=licencia_path,
            imagen=ultima_imagen_usada,
            publicar_en=programar_publicacion_exacta("oracion"),
            tag=tag_nuevo
        )
    else:
        print(f"[ERROR] No se pudo crear el archivo final: {path_out}")



# --------------------------------------------
#                VIDEO SALMO
# --------------------------------------------

def crear_video_salmo(path_in, path_out):
    img_fija, mus_fija = obtener_parametros_opcionales()

    # Leer contenido
    with open(path_in, "r", encoding="utf-8") as f:
        texto = f.read()

    # Obtener nombre base del archivo
    base = os.path.splitext(os.path.basename(path_in))[0]
    partes = base.split("_")

    # EXTRAER NÚMERO DEL SALMO CORRECTAMENTE
    numero = next((p for p in partes if p.isdigit()), None)

    if numero is None:
        print(f"[WARN] No se encontró número en el archivo {base}, usando '?'")
        numero = "?"

    # -------------------------------------------
    # 🔥 Construir nombre descriptivo del salmo
    #    Quitando "salmo" y el número del archivo
    # -------------------------------------------
    nombre_raw = (
        base.replace("salmo", "")
            .replace(numero, "")
            .replace("_", " ")
            .strip()
    )

    # Correcciones comunes (ñ, Dios, etc.)
    nombre_raw = (
        nombre_raw.lower()
            .replace("senor", "señor")
            .replace("dios", "Dios")
    )

    # Capitalización bonita
    nombre = nombre_raw.title()

    
    # -------------------------------
    # 🔥 Título final con “Salmo” bien escrito
    # -------------------------------
    titulo = f"Salmo {numero} — {nombre}"

    # Dividir en estrofas
    estrofas = [e.strip() for e in texto.split("\n\n") if e.strip()]
    estrofas = estrofas[:MAX_ESTROFAS]

    # Duración total
    if MODO_TEST:
        dur_total = 2
    else:
        dur_total = len(estrofas) * SEGUNDOS_ESTROFA

    # Fondo + gradiente
    fondo, grad = crear_fondo(dur_total, img_fija)

    # Título como imagen
    crear_imagen_titulo(titulo, "titulo.png")
    titulo_clip = (
        ImageClip("titulo.png")
        .set_duration(dur_total)
        .set_position(("center", 120))
        .set_opacity(1)
    )

    # Clips de estrofas
    clips = []
    t = 0
    for e in estrofas:
        crear_imagen_texto(e, "estrofa.png")

        # Reemplazar ñ dentro del contenido si hiciera falta
        e = (
            e.replace("senor", "señor")
             .replace("Senor", "Señor")
             .replace("dios", "Dios")
        )

        dur_e = 2 if MODO_TEST else SEGUNDOS_ESTROFA
        c = ImageClip("estrofa.png").set_duration(dur_e).set_position("center").set_opacity(1)

        if not MODO_TEST:
            c = c.fx(fadein, 0.8).set_start(t)

        clips.append(c)
        t += dur_e

    # Audio
    audio_duracion = dur_total + CTA_DUR
    audio, musica_usada = crear_audio(audio_duracion, mus_fija)

    licencia_path = f"musica/licence/licence_{musica_usada.replace('.mp3','')}.txt"

    tag_nuevo = generar_tag_inteligente(
        tipo="salmo",
        texto=texto,
        imagen=ultima_imagen_usada,
        musica=musica_usada,
        duracion=audio_duracion
    )

    intentos = 0
    while tag_ya_existe(tag_nuevo) and intentos < 5:
        print("⚠ TAG duplicado → regenerando música e imagen...")

        # Regenerar imagen
        fondo, grad = crear_fondo(dur_total, None)
        imagen_regenerada = ultima_imagen_usada  # sincronización real

        audio, musica_usada = crear_audio(audio_duracion, None)

        tag_nuevo = generar_tag_inteligente(
            tipo="salmo",
            texto=texto,
            imagen=imagen_regenerada,
            musica=musica_usada,
            duracion=audio_duracion
        )
        intentos += 1

    crear_video_base(fondo, grad, titulo_clip, audio, clips, path_out)

    if os.path.exists(path_out):
        registrar_video_generado(
            archivo_video=path_out,
            tipo="salmo",
            musica=musica_usada,
            licencia=licencia_path,
            imagen=ultima_imagen_usada,
            publicar_en=programar_publicacion_exacta("salmo"),
            tag=tag_nuevo
        )
    else:
        print(f"[ERROR] No se pudo crear el archivo final: {path_out}")


# --------------------------------------------
#          CREAR VARIOS ALEATORIOS
# --------------------------------------------




def crear_videos_del_dia(cantidad, modo):
    historial = cargar_historial()  # IMPORTANTE: cargar historial real

    carpeta = "textos/salmos" if modo == "salmo" else "textos/oraciones"

    for _ in range(cantidad):

        # 1) Selección de archivo SIN repetir 7 días
        elegido = elegir_no_repetido(carpeta, historial)

        entrada = f"{carpeta}/{elegido}"
        base = elegido.replace(".txt", "")

        subfolder = "oraciones" if modo == "oracion" else "salmos"
        salida = f"videos/{subfolder}/{base}.mp4"

        print(f" Generando ({modo}) → {salida}")

        if modo == "salmo":
            crear_video_salmo(entrada, salida)
        else:
            crear_video_oracion(entrada, salida)

        # Guardar SOLO textos_usados
        hist_actual = cargar_historial()  # historial real actualizado por registrar_video_generado
        hist_actual["textos_usados"] = historial["textos_usados"]
        guardar_historial(hist_actual)

        limpiar_temporales()

    print("[DEBUG] crear_videos_del_dia(): OK con control de repetición")



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

    modo = sys.argv[1].lower() if len(sys.argv) > 2 else None

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
