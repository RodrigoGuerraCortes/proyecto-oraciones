# generator/v3/integrations/facebook_api.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()

FB_API_VERSION = os.getenv("FB_API_VERSION", "v24.0")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")


def subir_reel_facebook(*, ruta_video, descripcion, scheduled_publish_time):

    if not FB_PAGE_ID or not FB_PAGE_ACCESS_TOKEN:
        raise RuntimeError("Faltan credenciales de Facebook")

    base_url = f"https://graph.facebook.com/{FB_API_VERSION}"

    with open(ruta_video, "rb") as f:
        file_bytes = f.read()

    file_size = len(file_bytes)

    # START
    init_url = f"{base_url}/{FB_PAGE_ID}/video_reels"
    r1 = requests.post(
        init_url,
        params={
            "access_token": FB_PAGE_ACCESS_TOKEN,
            "upload_phase": "start",
            "file_size": file_size,
        },
    )
    r1.raise_for_status()
    data = r1.json()

    upload_url = data["upload_url"]
    video_id = data["video_id"]

    # UPLOAD
    headers = {
        "Authorization": f"OAuth {FB_PAGE_ACCESS_TOKEN}",
        "Offset": "0",
        "X-Entity-Length": str(file_size),
        "X-Entity-Name": video_id,
        "Content-Type": "video/mp4",
        "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
    }

    requests.post(upload_url, headers=headers, data=file_bytes).raise_for_status()

    # FINISH
    r3 = requests.post(
        init_url,
        params={
            "access_token": FB_PAGE_ACCESS_TOKEN,
            "upload_phase": "finish",
            "video_id": video_id,
            "description": descripcion,
            "scheduled_publish_time": scheduled_publish_time,
            "video_state": "SCHEDULED",
        },
    )
    r3.raise_for_status()

    return video_id
