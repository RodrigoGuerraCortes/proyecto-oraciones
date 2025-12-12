#!/usr/bin/env python3
import os
import sys
from datetime import datetime

import requests
from dotenv import load_dotenv

from generar_descripcion import generar_descripcion
from logic.historial_util import (
    obtener_siguiente_video_para,
    marcar_como_publicado,
    convertir_fecha_para,
)

# =====================================================
# CONFIG
# =====================================================
load_dotenv()

FB_API_VERSION = os.getenv("FB_API_VERSION", "v24.0")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")


if not FB_PAGE_ID or not FB_PAGE_ACCESS_TOKEN:
    print("[ERROR] Faltan variables de entorno FB_PAGE_ID o FB_PAGE_ACCESS_TOKEN")
    sys.exit(1)


# =====================================================
# SUBIR ARCHIVO COMO REEL (upload_phase=start/upload/finish)
# =====================================================
def subir_reel_facebook(ruta_video: str, descripcion: str, scheduled_publish_time: int):

    base_url = f"https://graph.facebook.com/{FB_API_VERSION}"

    # Leer bytes y tamaño
    with open(ruta_video, "rb") as f:
        file_bytes = f.read()

    file_size = len(file_bytes)

    # -------------------------------------------------
    # 1) START — Inicializar la sesión
    # -------------------------------------------------
    init_url = f"{base_url}/{FB_PAGE_ID}/video_reels"
    init_params = {
        "access_token": FB_PAGE_ACCESS_TOKEN,
        "upload_phase": "start",
        "file_size": file_size,
    }

    print("🟡 [FB] Inicializando subida...")
    r1 = requests.post(init_url, params=init_params)
    r1.raise_for_status()
    data_start = r1.json()

    upload_url = data_start["upload_url"]     # rupload.facebook.com/...
    video_id = data_start["video_id"]

    print(f"✅ [FB] Sesión iniciada. video_id={video_id}")

    # -------------------------------------------------
    # 2) UPLOAD — Enviar video en un solo chunk
    # -------------------------------------------------
    print("🟡 [FB] Subiendo archivo binario...")

    upload_headers = {
        "Authorization": f"OAuth {FB_PAGE_ACCESS_TOKEN}",
        "Offset": "0",
        "X-Entity-Length": str(file_size),
        "X-Entity-Name": video_id,
        "Content-Type": "video/mp4",
        "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
    }

    r2 = requests.post(upload_url, headers=upload_headers, data=file_bytes)
    r2.raise_for_status()

    print("✅ [FB] Subida binaria completada")

    # -------------------------------------------------
    # 3) FINISH — Publicar el Reel (agendar)
    # -------------------------------------------------
    finish_url = f"{base_url}/{FB_PAGE_ID}/video_reels"
    finish_params = {
        "access_token": FB_PAGE_ACCESS_TOKEN,
        "upload_phase": "finish",
        "video_id": video_id,
        "description": descripcion,
        "scheduled_publish_time": scheduled_publish_time,
        "video_state": "SCHEDULED",
    }

    print("🟡 [FB] Finalizando publicación...")
    r3 = requests.post(finish_url, params=finish_params)
    r3.raise_for_status()
    data_finish = r3.json()

    print("🎉 [FB] Reel programado correctamente:", data_finish)

    return video_id



# =====================================================
# 2. LÓGICA PRINCIPAL
# =====================================================
def subir_siguiente_video_facebook():

    video = obtener_siguiente_video_para("facebook")
    if video is None:
        print("✔ No hay videos pendientes para Facebook.")
        return

    archivo = video["archivo"]
    tipo = video.get("tipo", "oracion")
    publicar_en = video.get("publicar_en")

    # === Descripción especializada para Facebook ===
    descripcion = generar_descripcion(
        tipo,
        publicar_en,
        archivo,
        plataforma="facebook",
    )

    # === Conversión a UNIX ===
    unix_date = convertir_fecha_para("facebook", publicar_en)

    print(f"\n📤 [FB] Subiendo Reel para Facebook:")
    print(f"   Archivo: {archivo}")
    print(f"   Publicar en: {publicar_en} (unix={unix_date})")

    # === SUBIR ===
    video_id = subir_reel_facebook(
        ruta_video=archivo,
        descripcion=descripcion,
        scheduled_publish_time=unix_date,
    )

    # === Actualizar estado ===
    marcar_como_publicado("facebook", archivo, video_id)

    print("\n✔ [FB] Reel programado y marcado como publicado.\n")


# =====================================================
# ENTRYPOINT
# =====================================================
if __name__ == "__main__":
    subir_siguiente_video_facebook()
