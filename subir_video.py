import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# -------- CONFIG --------
CLIENT_SECRETS_FILE = "client_secret.json"
TOKEN_FILE = "token.pickle"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def obtener_servicio_youtube():
    creds = None

    # Si ya existe el token guardado, úsalo
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    # Si no hay token, inicia el flujo OAuth
    if not creds:
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, SCOPES
        )
        creds = flow.run_local_server(port=0)

        # Guarda token refrescable
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    return build("youtube", "v3", credentials=creds)


def subir_video(ruta_video, titulo, descripcion, tags=None, privacidad="private"):
    youtube = obtener_servicio_youtube()

    request_body = {
        "snippet": {
            "title": titulo,
            "description": descripcion,
            "tags": tags or ["oracion", "reflexion", "catolico", "biblia"]
        },
        "status": {
            "privacyStatus": privacidad
        }
    }

    media = MediaFileUpload(ruta_video, chunksize=1024*1024, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media
    )

    print("📤 Subiendo video a YouTube...")

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Progreso: {int(status.progress() * 100)}%")

    print("🎉 Video subido con éxito")
    print("➡ ID del video:", response.get("id"))

    return response


# -------- EJEMPLO DE USO --------
if __name__ == "__main__":
    subir_video(
        ruta_video="videos/video_20251127_1_oracion.mp4",
        titulo="Oración del día - 1 minuto 🙏✨",
        descripcion="Una oración diaria para acompañarte en tu camino espiritual. ",
        tags=["oracion diaria", "reflexion", "catolico", "jesus"],
        privacidad="public"
    )
