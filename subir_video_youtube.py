import os
import json
import pickle
import shutil
import sys
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaFileUpload
from openai import OpenAI

from generar_descripcion import generar_descripcion, generar_tags_from_descripcion

# -------- CONFIG --------
CLIENT_SECRETS_FILE = "client_secret.json"
TOKEN_FILE = "token.pickle"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
HISTORIAL = "historial.json"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# =====================================================
#   CARGAR / GUARDAR HISTORIAL (NO ALTERADO)
# =====================================================
def cargar_historial():
    if not os.path.exists(HISTORIAL):
        return {"pendientes": [], "publicados": []}

    with open(HISTORIAL, "r") as f:
        contenido = f.read().strip()
        if not contenido:
            return {"pendientes": [], "publicados": []}

        data = json.loads(contenido)
        data.setdefault("pendientes", [])
        data.setdefault("publicados", [])
        return data


def guardar_historial(data):
    with open(HISTORIAL, "w") as f:
        json.dump(data, f, indent=4)


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
            CLIENT_SECRETS_FILE, SCOPES
        )
        creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    return build("youtube", "v3", credentials=creds)


# =====================================================
# 2. SUBIR VIDEO A YOUTUBE
# =====================================================
def subir_video_youtube(ruta_video, titulo, descripcion, tags, privacidad, publish_at):

    youtube = obtener_servicio_youtube()

    if publish_at:
        status_body = {
            "privacyStatus": "private",
            "publishAt": publish_at
        }
        print(f"⏰ Programando para: {publish_at}")
    else:
        status_body = {"privacyStatus": privacidad}

    request_body = {
        "snippet": {
            "title": titulo,
            "description": descripcion,
            "tags": tags,
            "categoryId": "22"
        },
        "status": status_body
    }

    media = MediaFileUpload(ruta_video, chunksize=1024*1024, resumable=True)

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
# 3. INICIALIZAR ESTRUCTURA DE PLATAFORMAS
# =====================================================
def asegurar_plataformas(video):
    """
    Garantiza que cada pendiente tenga la estructura:
       "plataformas": {
            "youtube": {...},
            "facebook": {...},
            "instagram": {...},
            "tiktok": {...}
       }
    """

    if "plataformas" not in video:
        video["plataformas"] = {}

    for p in ("youtube", "facebook", "instagram", "tiktok"):
        if p not in video["plataformas"]:
            video["plataformas"][p] = {
                "estado": "pendiente",
                "video_id": None,
                "fecha_publicado": None
            }

    return video


# =====================================================
# 4. OBTENER SIGUIENTE VIDEO PARA YOUTUBE
# =====================================================
def obtener_siguiente_para_youtube():
    hist = cargar_historial()

    if not hist["pendientes"]:
        print("\n✔ No hay videos pendientes.")
        return None

    candidatos = []
    for v in hist["pendientes"]:
        v = asegurar_plataformas(v)
        if v["plataformas"]["youtube"]["estado"] == "pendiente":
            candidatos.append(v)

    if not candidatos:
        print("\n✔ No hay videos pendientes para YouTube.")
        return None

    # Ordenar por publicar_en
    def ordenar(x):
        try:
            dt = datetime.fromisoformat(x["publicar_en"])
            return dt.timestamp()
        except:
            return float("inf")

    candidatos.sort(key=ordenar)
    return candidatos[0]


# =====================================================
# 5. PROCESO PRINCIPAL DE SUBIDA
# =====================================================
def subir_siguiente_youtube(privacidad="public"):
    hist = cargar_historial()
    video = obtener_siguiente_para_youtube()

    if video is None:
        return

    archivo = video["archivo"]
    tipo = video["tipo"]

    titulo_base = os.path.splitext(os.path.basename(archivo))[0]
    titulo = f"{titulo_base.replace('_', ' ').title()} — 1 minuto 🙏✨"

    descripcion = generar_descripcion(tipo, video["publicar_en"], archivo)
    tags = generar_tags_from_descripcion(descripcion)

    publish_at = video["publicar_en"]

    youtube_id = subir_video_youtube(
        archivo,
        titulo,
        descripcion,
        tags,
        privacidad=privacidad,
        publish_at=publish_at
    )

    # Actualizar historial
    for p in hist["pendientes"]:
        if p["archivo"] == archivo:
            p = asegurar_plataformas(p)
            p["plataformas"]["youtube"] = {
                "estado": "publicado",
                "video_id": youtube_id,
                "fecha_publicado": datetime.now().isoformat()
            }

    guardar_historial(hist)

    print("\n✔ YouTube: estado actualizado en historial.\n")


# =====================================================
# 6. EJECUCIÓN MANUAL
# =====================================================
if __name__ == "__main__":

    if "--privado" in sys.argv:
        privacidad_forzada = "private"
    elif "--oculto" in sys.argv:
        privacidad_forzada = "unlisted"
    elif "--publico" in sys.argv:
        privacidad_forzada = "public"
    else:
        privacidad_forzada = "public"

    subir_siguiente_youtube(privacidad_forzada)
