#!/usr/bin/env python3
import os
import json
import time
import subprocess
from datetime import datetime

# Importamos SOLO utilidades centralizadas
from logic.historial_util import (
    asegurar_plataformas,
    cargar_historial,
    guardar_historial,
    mover_a_publicados,     # usamos la versión oficial y segura
)

HISTORIAL = "historial.json"
LOG_DIR = "logs/subir_videos"
CHECK_INTERVAL = 5
MAX_REINTENTOS = 3


# ---------------------------------------------------------
# Logging central
# ---------------------------------------------------------
def log(msg):
    os.makedirs(LOG_DIR, exist_ok=True)
    path = os.path.join(LOG_DIR, "master.log")

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(path, "a") as f:
        f.write(f"[{ts}] {msg}\n")

    print(msg)


# ---------------------------------------------------------
# Obtener fechas pendientes
# ---------------------------------------------------------
def obtener_fechas_pendientes(hist):
    fechas = set()
    for v in hist["pendientes"]:
        try:
            fechas.add(datetime.fromisoformat(v["publicar_en"]).date())
        except:
            pass
    return sorted(fechas)


# ---------------------------------------------------------
# Seleccionar día de publicación
# ---------------------------------------------------------
def seleccionar_dia_publicacion():
    hist = cargar_historial()
    fechas = obtener_fechas_pendientes(hist)
    hoy = datetime.now().date()

    if hoy in fechas:
        log(f"📌 Día seleccionado: HOY {hoy}")
        return hoy

    for f in fechas:
        if f >= hoy:
            log(f"📌 Día seleccionado: {f} (próximo disponible)")
            return f

    log("✔ No hay videos pendientes.")
    return None


# ---------------------------------------------------------
# Obtener videos del día
# ---------------------------------------------------------
def obtener_videos_del_dia(dia):
    hist = cargar_historial()
    seleccion = []

    for v in hist["pendientes"]:
        try:
            if datetime.fromisoformat(v["publicar_en"]).date() == dia:
                seleccion.append(v)
        except:
            pass

    seleccion.sort(key=lambda v: datetime.fromisoformat(v["publicar_en"]))
    return seleccion


# ---------------------------------------------------------
# Estado completo (pero NO exige Instagram/TikTok)
# ---------------------------------------------------------
def plataformas_completas(video):
    """
    COMPLETADO = YouTube + Facebook + Instagram publicados.
    TikTok aún no se considera obligatorio.
    """
    p = video.get("plataformas", {})

    requerido = ["youtube", "facebook", "instagram"]

    for plataforma in requerido:
        estado = p.get(plataforma, {}).get("estado")
        if estado != "publicado":
            return False

    return True


# ---------------------------------------------------------
# Detectar fallos (solo YT y FB)
# ---------------------------------------------------------
def plataforma_fallida(video):
    p = video.get("plataformas", {})

    for plataforma in ("youtube", "facebook", "instagram"):
        if p.get(plataforma, {}).get("estado") == "fallido":
            return True

    return False


# ---------------------------------------------------------
# Lanzar subidas en paralelo (solo YT + FB)
# ---------------------------------------------------------
def lanzar_subidas(video):
    log(f"🚀 Lanzando subida para: {video['archivo']}")

    procesos = {
        "youtube": subprocess.Popen(
            ["python3", "subir_video_youtube.py"],
            stdout=open(os.path.join(LOG_DIR, "youtube.log"), "a"),
            stderr=subprocess.STDOUT
        ),
        "facebook": subprocess.Popen(
            ["python3", "subir_video_facebook.py"],
            stdout=open(os.path.join(LOG_DIR, "facebook.log"), "a"),
            stderr=subprocess.STDOUT
        ),
        "instagram": subprocess.Popen(
            ["python3", "subir_video_instagram.py"],
            stdout=open(os.path.join(LOG_DIR, "instagram.log"), "a"),
            stderr=subprocess.STDOUT
        )
    }

    return procesos



# ---------------------------------------------------------
# Reintentos automáticos si falla YT o FB o INSTAGRAM
# ---------------------------------------------------------
def reintentar_plataformas(video):
    hist = cargar_historial()

    for plataforma in ("youtube", "facebook", "instagram"):
        datos = video["plataformas"][plataforma]

        if datos["estado"] == "fallido":

            datos["reintentos"] = datos.get("reintentos", 0)

            if datos["reintentos"] < MAX_REINTENTOS:
                datos["reintentos"] += 1
                guardar_historial(hist)

                log(f"🔁 Reintentando {plataforma} ({datos['reintentos']}/{MAX_REINTENTOS})...")

                subprocess.Popen(["python3", f"subir_video_{plataforma}.py"])

            else:
                log(f"❌ Plataforma {plataforma} agotó reintentos.")

    guardar_historial(hist)



# ---------------------------------------------------------
# Lógica principal
# ---------------------------------------------------------
def main():

    dia = seleccionar_dia_publicacion()
    if not dia:
        return

    videos = obtener_videos_del_dia(dia)

    for video in videos:

        # aseguramos estructura correcta del historial
        video = asegurar_plataformas(video)

        # lanzar subidas paralelas (YT + FB)
        lanzar_subidas(video)
        time.sleep(3)
        # Espera activa hasta que se complete o falle
        while True:

            time.sleep(CHECK_INTERVAL)

            hist = cargar_historial()
            refreshed = next((v for v in hist["pendientes"] if v["archivo"] == video["archivo"]), None)

            if refreshed is None:
                break  # Ya movido por otro proceso

            if plataforma_fallida(refreshed):
                reintentar_plataformas(refreshed)

            if plataformas_completas(refreshed):
                mover_a_publicados(refreshed)
                break


if __name__ == "__main__":
    main()
