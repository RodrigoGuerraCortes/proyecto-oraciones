#!/usr/bin/env python3
import os
import sys
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

from generar_descripcion import generar_descripcion
from logic.historial_util import (
    obtener_siguiente_video_para,
    marcar_como_publicado,
    marcar_como_pendiente,
    marcar_como_procesando,
    convertir_fecha_para,
)

# =====================================================
# CONFIG
# =====================================================
load_dotenv()

TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN")  # OAuth access token
if not TIKTOK_ACCESS_TOKEN:
    print("❌ Falta TIKTOK_ACCESS_TOKEN en .env")
    sys.exit(1)

BASE_URL = "https://open.tiktokapis.com/v2/post/publish/video"

# =====================================================
# 1. CREAR CONTENEDOR TIKTOK (INIT)
# =====================================================
def crear_contenedor_tiktok(descripcion: str, publish_time: int | None):
    url = f"{BASE_URL}/init/"

    payload = {
        "post_info": {
            "title": descripcion[:150],
            "privacy_level": "PUBLIC",
            "disable_comment": False,
            "disable_duet": False,
            "disable_stitch": False
        },
        "source_info": {
            "source": "FILE_UPLOAD"
        }
    }

    if publish_time:
        payload["post_info"]["publish_time"] = publish_time

    headers = {
        "Authorization": f"Bearer {TIKTOK_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    print("🟡 [TikTok] Creando contenedor...")
    r = requests.post(url, json=payload, headers=headers)

    try:
        r.raise_for_status()
    except Exception:
        print("❌ ERROR creando contenedor TikTok:")
        print(r.text)
        raise

    data = r.json()["data"]
    publish_id = data["publish_id"]
    upload_url = data["upload_url"]

    print(f"✅ [TikTok] Contenedor creado. publish_id={publish_id}")
    return publish_id, upload_url


# =====================================================
# 2. SUBIR VIDEO (PUT DIRECTO)
# =====================================================
def subir_video_tiktok(upload_url: str, ruta_video: str):
    print("🟡 [TikTok] Subiendo video...")

    with open(ruta_video, "rb") as f:
        r = requests.put(upload_url, data=f)

    try:
        r.raise_for_status()
    except Exception:
        print("❌ ERROR subiendo video a TikTok:")
        print(r.text)
        raise

    print("🎉 [TikTok] Video subido correctamente.")


# =====================================================
# 3. LÓGICA PRINCIPAL
# =====================================================
def subir_siguiente_video_tiktok():
    video = obtener_siguiente_video_para("tiktok")

    if video is None:
        print("✔ No hay videos pendientes para TikTok.")
        return

    archivo = video["archivo"]
    tipo = video.get("tipo", "oracion")
    publicar_en = video.get("publicar_en")

    print("\n📤 [TikTok] Subiendo video")
    print(f"   Archivo: {archivo}")
    print(f"   Publicar en: {publicar_en}")

    # 🔒 1️⃣ Bloqueo inmediato
    marcar_como_procesando("tiktok", archivo)

    try:
        descripcion = generar_descripcion(
            tipo=tipo,
            hora_texto=publicar_en,
            archivo_texto=archivo,
            plataforma="tiktok"
        )

        publish_time = convertir_fecha_para("tiktok", publicar_en)

        # 2️⃣ Crear contenedor
        publish_id, upload_url = crear_contenedor_tiktok(
            descripcion=descripcion,
            publish_time=publish_time
        )

        # 3️⃣ Subir MP4
        subir_video_tiktok(upload_url, archivo)

        # 4️⃣ Marcar como publicado
        marcar_como_publicado("tiktok", archivo, publish_id)

        print("\n✔ [TikTok] Video publicado / programado correctamente.\n")

    except Exception as e:
        marcar_como_pendiente("tiktok", archivo)
        print(f"❌ [TikTok] Error. Se revierte a pendiente: {e}")
        raise


# =====================================================
# ENTRYPOINT
# =====================================================
if __name__ == "__main__":
    subir_siguiente_video_tiktok()
