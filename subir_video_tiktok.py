#!/usr/bin/env python3
import os
import requests
import pprint
from dotenv import load_dotenv

from generar_descripcion import generar_descripcion
from logic.historial_util import (
    obtener_siguiente_video_para,
    marcar_como_publicado,
    marcar_como_pendiente,
    marcar_como_procesando,
)
from generar_token_tiktok import get_access_token, is_tiktok_sandbox

# =====================================================
# CONFIG
# =====================================================
load_dotenv()

BASE_URL = "https://open.tiktokapis.com/v2/post/publish/inbox/video"

# =====================================================
# 1. CREAR CONTENEDOR (INBOX / SANDBOX)
# =====================================================
def crear_contenedor_tiktok(ruta_video: str):
    url = f"{BASE_URL}/init/"
    sandbox = is_tiktok_sandbox()

    if not sandbox:
        raise RuntimeError("Este script está preparado SOLO para SANDBOX / INBOX")

    video_size = os.path.getsize(ruta_video)

    payload = {
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": video_size,
            "chunk_size": video_size,
            "total_chunk_count": 1
        }
    }

    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json"
    }

    # 🔍 LOG REQUEST
    print("\n================ TIKTOK INIT REQUEST ================")
    print("ENV: SANDBOX")
    print("URL:", url)
    print("HEADERS:")
    pprint.pprint(headers)
    print("PAYLOAD:")
    pprint.pprint(payload)
    print("====================================================\n")

    r = requests.post(url, json=payload, headers=headers)

    # 🔍 LOG RESPONSE
    print("\n================ TIKTOK INIT RESPONSE ================")
    print("STATUS:", r.status_code)
    try:
        pprint.pprint(r.json())
    except Exception:
        print(r.text)
    print("====================================================\n")

    r.raise_for_status()

    data = r.json()["data"]
    return data["publish_id"], data["upload_url"]


# =====================================================
# 2. SUBIR VIDEO BINARIO
# =====================================================
def subir_video_tiktok(upload_url: str, ruta_video: str):
    video_size = os.path.getsize(ruta_video)

    headers = {
        "Content-Type": "video/mp4",
        "Content-Range": f"bytes 0-{video_size - 1}/{video_size}"
    }

    with open(ruta_video, "rb") as f:
        r = requests.put(upload_url, data=f, headers=headers)

    r.raise_for_status()


# =====================================================
# 3. FLUJO PRINCIPAL
# =====================================================
def subir_siguiente_video_tiktok():
    video = obtener_siguiente_video_para("tiktok")
    if not video:
        print("✔ No hay videos pendientes para TikTok.")
        return

    archivo = video["archivo"]
    tipo = video.get("tipo", "oracion")

    marcar_como_procesando("tiktok", archivo)

    try:
        # Generamos descripción SOLO para dejar trazabilidad,
        # TikTok INBOX no la usa (se edita en la app)
        _ = generar_descripcion(
            tipo=tipo,
            hora_texto=video.get("publicar_en"),
            archivo_texto=archivo,
            plataforma="tiktok"
        )

        publish_id, upload_url = crear_contenedor_tiktok(archivo)

        subir_video_tiktok(upload_url, archivo)

        marcar_como_publicado("tiktok", archivo, publish_id)
        print("🎉 TikTok (SANDBOX / INBOX) subido correctamente")

    except Exception as e:
        marcar_como_pendiente("tiktok", archivo)
        print(f"❌ Error TikTok, rollback aplicado: {e}")
        raise


# =====================================================
# ENTRYPOINT
# =====================================================
if __name__ == "__main__":
    subir_siguiente_video_tiktok()

