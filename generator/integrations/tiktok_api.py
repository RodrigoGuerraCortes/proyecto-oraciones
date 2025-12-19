#!/usr/bin/env python3
import os
import requests
import pprint
from dotenv import load_dotenv

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
    print({
        "Authorization": "Bearer ***REDACTED***",
        "Content-Type": headers.get("Content-Type")
    })
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

    print("[TIKTOK] Uploading video binary...")
    print(f"[TIKTOK] File size: {video_size} bytes")

    headers = {
        "Content-Type": "video/mp4",
        "Content-Range": f"bytes 0-{video_size - 1}/{video_size}"
    }

    with open(ruta_video, "rb") as f:
        r = requests.put(upload_url, data=f, headers=headers)

    print("[TIKTOK] Upload response status:", r.status_code)

    r.raise_for_status()

    print("[TIKTOK] Upload response status:", r.status_code)