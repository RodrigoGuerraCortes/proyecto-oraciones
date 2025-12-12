#!/usr/bin/env python3
import os
import sys
import requests
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import time

from generar_descripcion import generar_descripcion
from logic.historial_util import (
    obtener_siguiente_video_para,
    marcar_como_publicado,
    convertir_fecha_para,
    marcar_como_pendiente,
    marcar_como_procesando
)

# =====================================================
# CONFIG
# =====================================================
load_dotenv()

FB_API_VERSION = os.getenv("FB_API_VERSION", "v24.0")
IG_USER_ID = os.getenv("IG_USER_ID")
IG_ACCESS_TOKEN = os.getenv("FB_USER_ACCESS_TOKEN")  # Long-lived USER token

if not IG_USER_ID or not IG_ACCESS_TOKEN:
    print("[ERROR] Faltan IG_USER_ID o FB_USER_ACCESS_TOKEN en .env")
    sys.exit(1)

# Cloudinary config
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)


BASE_URL = f"https://graph.facebook.com/{FB_API_VERSION}"

# =====================================================
# 1. SUBIR VIDEO A CLOUDINARY
# =====================================================
def subir_video_cloudinary(ruta_video: str) -> str:
    print("🟡 [IG] Subiendo video a Cloudinary...")

    result = cloudinary.uploader.upload(
        ruta_video,
        resource_type="video",
        folder="instagram_reels"
    )

    video_url = result["secure_url"]
    print(f"✅ [IG] Video alojado en Cloudinary: {video_url}")

    return video_url


# =====================================================
# 2. CREAR CONTENEDOR IG (USANDO video_url)
# =====================================================
def crear_contenedor_instagram(video_url: str, descripcion: str) -> str:
    url = f"{BASE_URL}/{IG_USER_ID}/media"

    params = {
        "access_token": IG_ACCESS_TOKEN,
        "media_type": "REELS",
        "video_url": video_url,
        "caption": descripcion
    }

    print("🟡 [IG] Creando contenedor de Reel...")
    r = requests.post(url, data=params)

    try:
        r.raise_for_status()
    except Exception:
        print("❌ ERROR creando contenedor IG:")
        print(r.text)
        raise

    creation_id = r.json()["id"]
    print(f"✅ [IG] Contenedor creado. creation_id={creation_id}")

    return creation_id


# =====================================================
# 3. PROGRAMAR PUBLICACIÓN
# =====================================================
def programar_reel_instagram(creation_id: str, publish_time_unix: int):
    url = f"{BASE_URL}/{IG_USER_ID}/media_publish"

    params = {
        "access_token": IG_ACCESS_TOKEN,
        "creation_id": creation_id,
        "publish_time": publish_time_unix
    }

    print("🟡 [IG] Programando Reel...")
    r = requests.post(url, data=params)

    try:
        r.raise_for_status()
    except Exception:
        print("❌ ERROR programando Reel:")
        print(r.text)
        raise

    print("🎉 [IG] Reel programado correctamente.")
    print("Respuesta:", r.json())


# =====================================================
# 4. LÓGICA PRINCIPAL
# =====================================================
def subir_siguiente_video_instagram():
    video = obtener_siguiente_video_para("instagram")

    if video is None:
        print("✔ No hay videos pendientes para Instagram.")
        return

    archivo = video["archivo"]
    tipo = video.get("tipo", "oracion")
    publicar_en = video.get("publicar_en")

    print("\n📤 [IG] Subiendo Reel para Instagram")
    print(f"   Archivo: {archivo}")
    print(f"   Publicar en: {publicar_en}")

    # 🔒 1️⃣ BLOQUEO INMEDIATO (anti-duplicados)
    marcar_como_procesando("instagram", archivo)

    try:
        descripcion = generar_descripcion(
            tipo=tipo,
            hora_texto=publicar_en,
            archivo_texto=archivo,
            plataforma="instagram"
        )

        publish_time_unix = convertir_fecha_para("instagram", publicar_en)

        # 2️⃣ Subir a Cloudinary
        video_url = subir_video_cloudinary(archivo)

        # 3️⃣ Crear contenedor IG
        creation_id = crear_contenedor_instagram(video_url, descripcion)

        # 4️⃣ Esperar procesamiento
        esperar_media_listo(creation_id)

        # 5️⃣ Publicar (inmediato)
        programar_reel_instagram(creation_id, publish_time_unix)

        # 6️⃣ Marcar como publicado
        marcar_como_publicado("instagram", archivo, creation_id)

        print("\n✔ [IG] Reel publicado y marcado en historial.\n")

    except Exception as e:
        # 🔁 rollback limpio
        marcar_como_pendiente("instagram", archivo)
        print(f"❌ [IG] Error procesando video. Se revierte a pendiente: {e}")
        raise

# =====================================================
# Controlar estado del contenedor
# =====================================================


def esperar_media_listo(creation_id: str, timeout=180, interval=5):
    """
    Espera a que Instagram termine de procesar el video.
    Retorna True si queda FINISHED, lanza excepción si ERROR o timeout.
    """
    status_url = f"{BASE_URL}/{creation_id}"
    params = {
        "access_token": IG_ACCESS_TOKEN,
        "fields": "status_code"
    }

    print("🟡 [IG] Esperando procesamiento del video...")

    elapsed = 0
    while elapsed < timeout:
        r = requests.get(status_url, params=params)

        try:
            r.raise_for_status()
        except Exception:
            print("❌ ERROR consultando estado del media:")
            print(r.text)
            raise

        status = r.json().get("status_code")
        print(f"   ⏳ Estado actual: {status}")

        if status == "FINISHED":
            print("✅ [IG] Media listo para publicarse.")
            return True

        if status == "ERROR":
            raise RuntimeError("Instagram reportó ERROR procesando el video.")

        time.sleep(interval)
        elapsed += interval

    raise TimeoutError("Timeout esperando que Instagram procese el video.")





# =====================================================
# ENTRY POINT
# =====================================================
if __name__ == "__main__":
    subir_siguiente_video_instagram()
