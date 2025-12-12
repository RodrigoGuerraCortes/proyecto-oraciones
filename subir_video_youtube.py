#!/usr/bin/env python3
import os
import sys
import pickle
from datetime import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaFileUpload
from openai import OpenAI

# Helpers centralizados
from logic.historial_util import (
    obtener_siguiente_video_para,
    marcar_como_publicado,
    convertir_fecha_para,
)

from generar_descripcion import generar_descripcion, generar_tags_from_descripcion


# =====================================================
# CONFIG
# =====================================================
CLIENT_SECRETS_FILE = "client_secret.json"
TOKEN_FILE = "token.pickle"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# =====================================================
# 1. AUTENTICAR YOUTUBE
# =====================================================
def obtener_servicio_youtube():
    creds = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    if not creds:
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            SCOPES
        )
        creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    return build("youtube", "v3", credentials=creds)


# =====================================================
# 2. SUBIR VIDEO A YOUTUBE
# =====================================================
def subir_video_youtube(ruta, titulo, descripcion, tags, privacidad, publish_at):
    youtube = obtener_servicio_youtube()

    status_body = (
        {"privacyStatus": "private", "publishAt": publish_at}
        if publish_at else
        {"privacyStatus": privacidad}
    )

    request_body = {
        "snippet": {
            "title": titulo,
            "description": descripcion,
            "tags": tags,
            "categoryId": "22"
        },
        "status": status_body
    }

    media = MediaFileUpload(ruta, chunksize=1024 * 1024, resumable=True)

    print(f"\n📤 Subiendo video a YouTube...")

    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Progreso: {int(status.progress() * 100)}%")

    print("\n🎉 Video subido correctamente")
    return response.get("id")


# =====================================================
# 3. PROCESO PRINCIPAL
# =====================================================
def subir_siguiente_youtube(privacidad="public"):

    video = obtener_siguiente_video_para("youtube")
    if video is None:
        print("✔ No hay videos pendientes para YouTube.")
        return
    
    archivo = video["archivo"]
    tipo = video["tipo"]
    licencia = video["licencia"]

    # === generar título y descripción ===
    titulo_base = os.path.splitext(os.path.basename(archivo))[0]
    titulo = f"{titulo_base.replace('_', ' ').title()} — 1 minuto 🙏✨"

    descripcion = generar_descripcion(
                                        tipo, 
                                        video["publicar_en"], 
                                        archivo, 
                                        plataforma="youtube",
                                        licence=licencia
                                    )
    tags = generar_tags_from_descripcion(descripcion)

    # === convertir fecha si es necesario ===
    publish_at = convertir_fecha_para("youtube", video["publicar_en"])

    # === subir ===
    youtube_id = subir_video_youtube(
        ruta=archivo,
        titulo=titulo,
        descripcion=descripcion,
        tags=tags,
        privacidad=privacidad,
        publish_at=publish_at
    )

    # === marcar como publicado ===
    marcar_como_publicado("youtube", archivo, youtube_id)

    print("\n✔ YouTube: estado actualizado en historial.\n")


# =====================================================
# 4. ENTRYPOINT
# =====================================================
if __name__ == "__main__":

    if "--privado" in sys.argv:
        privacidad = "private"
    elif "--oculto" in sys.argv:
        privacidad = "unlisted"
    elif "--publico" in sys.argv:
        privacidad = "public"
    else:
        privacidad = "public"

    subir_siguiente_youtube(privacidad)
