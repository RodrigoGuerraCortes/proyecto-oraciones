# generator/v3/integrations/instagram_api.py

import os
import time
import requests
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

FB_API_VERSION = os.getenv("FB_API_VERSION", "v24.0")
IG_USER_ID = os.getenv("IG_USER_ID")
IG_ACCESS_TOKEN = os.getenv("FB_USER_ACCESS_TOKEN")

BASE_URL = f"https://graph.facebook.com/{FB_API_VERSION}"

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)


def subir_video_cloudinary(ruta_video: str) -> str:
    result = cloudinary.uploader.upload(
        ruta_video,
        resource_type="video",
        folder="instagram_reels"
    )
    return result["secure_url"]


def crear_contenedor_instagram(video_url: str, descripcion: str) -> str:
    r = requests.post(
        f"{BASE_URL}/{IG_USER_ID}/media",
        data={
            "access_token": IG_ACCESS_TOKEN,
            "media_type": "REELS",
            "video_url": video_url,
            "caption": descripcion,
        },
    )
    r.raise_for_status()
    return r.json()["id"]


def esperar_media_listo(creation_id: str, timeout=180, interval=5):
    status_url = f"{BASE_URL}/{creation_id}"
    elapsed = 0

    while elapsed < timeout:
        r = requests.get(
            status_url,
            params={
                "access_token": IG_ACCESS_TOKEN,
                "fields": "status_code",
            },
        )
        r.raise_for_status()

        status = r.json().get("status_code")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise RuntimeError("Instagram reportó ERROR procesando el video.")

        time.sleep(interval)
        elapsed += interval

    raise TimeoutError("Timeout esperando procesamiento de Instagram.")


def publicar_reel_instagram(creation_id: str):
    r = requests.post(
        f"{BASE_URL}/{IG_USER_ID}/media_publish",
        data={
            "access_token": IG_ACCESS_TOKEN,
            "creation_id": creation_id,
        },
    )
    r.raise_for_status()
    return r.json()
