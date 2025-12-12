#!/usr/bin/env python3
import os
import json
import time
import subprocess
from datetime import datetime

HISTORIAL = "historial.json"
LOG_DIR = "logs/subir_videos"
CHECK_INTERVAL = 5   # segundos entre revisiones del historial


# ---------------------------------------------------------
# Utils de historial
# ---------------------------------------------------------
def cargar_historial():
    if not os.path.exists(HISTORIAL):
        return {"pendientes": [], "publicados": []}

    with open(HISTORIAL, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_historial(data):
    with open(HISTORIAL, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------
def log(msg):
    os.makedirs(LOG_DIR, exist_ok=True)
    path = os.path.join(LOG_DIR, "master.log")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(path, "a") as f:
        f.write(f"[{ts}] {msg}\n")
    print(msg)


# ---------------------------------------------------------
# Obtener la lista de fechas disponibles
# ---------------------------------------------------------
def obtener_fechas_pendientes(hist):
    fechas = set()
    for v in hist["pendientes"]:
        try:
            dt = datetime.fromisoformat(v["publicar_en"])
            fechas.add(dt.date())
        except:
            pass
    return sorted(fechas)


# ---------------------------------------------------------
# Obtener el día que se debe publicar
# ---------------------------------------------------------
def seleccionar_dia_publicacion():
    hist = cargar_historial()
    fechas = obtener_fechas_pendientes(hist)
    hoy = datetime.now().date()

    # 1) ¿Hay videos para hoy?
    if hoy in fechas:
        log(f"📌 Día seleccionado: HOY {hoy}")
        return hoy

    # 2) Si no → usar el día más cercano hacia adelante
    for f in fechas:
        if f >= hoy:
            log(f"📌 Día seleccionado: {f} (próximo disponible)")
            return f

    log("✔ No hay videos pendientes para publicar.")
    return None


# ---------------------------------------------------------
# Filtrar videos del día
# ---------------------------------------------------------
def obtener_videos_del_dia(dia):
    hist = cargar_historial()
    seleccion = []
    for v in hist["pendientes"]:
        try:
            dt = datetime.fromisoformat(v["publicar_en"])
            if dt.date() == dia:
                seleccion.append(v)
        except:
            pass
    # Ordenarlos por hora
    seleccion.sort(key=lambda v: datetime.fromisoformat(v["publicar_en"]))
    return seleccion


# ---------------------------------------------------------
# Verifica si todas las plataformas están completas
# ---------------------------------------------------------
def plataformas_completas(video):
    p = video.get("plataformas", {})
    for plataforma in ("youtube", "facebook", "instagram", "tiktok"):
        estado = p.get(plataforma, {}).get("estado")
        if estado != "publicado":
            return False
    return True


# ---------------------------------------------------------
# Subir un video a todas las plataformas en paralelo
# ---------------------------------------------------------
def lanzar_subidas(video):
    log(f"🚀 Lanzando subida para: {video['archivo']}")

    procesos = []

    # YOUTUBE
    procesos.append(subprocess.Popen(
        ["python3", "subir_video_youtube.py"],
        stdout=open(os.path.join(LOG_DIR, "youtube.log"), "a"),
        stderr=subprocess.STDOUT
    ))

    # FACEBOOK
    procesos.append(subprocess.Popen(
        ["python3", "subir_video_facebook.py"],
        stdout=open(os.path.join(LOG_DIR, "facebook.log"), "a"),
        stderr=subprocess.STDOUT
    ))

    # En el futuro:
    # procesos.append(subprocess.Popen([... instagram ...]))
    # procesos.append(subprocess.Popen([... tiktok ...]))

    return procesos


# ---------------------------------------------------------
# Mover a publicados cuando todas las plataformas estén listas
# ---------------------------------------------------------
def mover_a_publicados(video):
    hist = cargar_historial()

    # eliminar de pendientes
    hist["pendientes"] = [v for v in hist["pendientes"] if v["archivo"] != video["archivo"]]

    # agregar a publicados
    hist["publicados"].append(video)

    guardar_historial(hist)

    log(f"✔ Movido a publicados: {video['archivo']}")


# ---------------------------------------------------------
# Lógica principal
# ---------------------------------------------------------
def main():
    dia = seleccionar_dia_publicacion()
    if not dia:
        return

    videos = obtener_videos_del_dia(dia)

    for video in videos:
        procesos = lanzar_subidas(video)

        # Esperar hasta que las plataformas terminen
        while True:
            time.sleep(CHECK_INTERVAL)
            hist = cargar_historial()
            refreshed_video = next(v for v in hist["pendientes"] if v["archivo"] == video["archivo"])

            if plataformas_completas(refreshed_video):
                log(f"🎉 TODAS las plataformas completaron: {video['archivo']}")
                mover_a_publicados(refreshed_video)
                break


if __name__ == "__main__":
    main()
