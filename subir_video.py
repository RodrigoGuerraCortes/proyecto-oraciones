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
# 1. GENERAR FECHA PROGRAMADA RFC3339
# =====================================================
def programar_publicacion(hora_str):
    ahora = datetime.now()

    pub = datetime.strptime(f"{ahora.date()} {hora_str}", "%Y-%m-%d %H:%M")

    if pub <= ahora:
        pub = pub + timedelta(days=1)

    return pub.strftime("%Y-%m-%dT%H:%M:%S-03:00")


# =====================================================
# 2. MOVER A CARPETA PUBLICADOS
# =====================================================
def mover_a_publicados(ruta, tipo):
    base = os.path.basename(ruta)
    destino_carpeta = os.path.join("videos", "publicados", tipo + "s")
    os.makedirs(destino_carpeta, exist_ok=True)

    destino = os.path.join(destino_carpeta, base)

    try:
        shutil.move(ruta, destino)
        print(f"📦 Video movido a: {destino}")
    except Exception as e:
        print(f"[ERROR] No se pudo mover a publicados: {e}")


# =====================================================
# 3. AUTENTICAR CON YOUTUBE
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
# 4. CARGAR / GUARDAR HISTORIAL
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
# 5. SUBIR VIDEO (CON SOPORTE PROGRAMADO / PRIVADO / OCULTO)
# =====================================================
def subir_video_youtube(ruta_video, titulo, descripcion, tags, privacidad, publish_at):
    youtube = obtener_servicio_youtube()

    # ⭐ Lógica correcta según documentación oficial de YouTube API
    if publish_at:
        status_body = {
            "privacyStatus": "private",   # obligatorio para programar
            "publishAt": publish_at
        }
        print(f"⏰ Programando para: {publish_at}")
    else:
        status_body = {
            "privacyStatus": privacidad
        }

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

    print(f"\n📤 Subiendo video...")

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
# 6. OBTENER SIGUIENTE VIDEO A PUBLICAR
# =====================================================
def obtener_siguiente_video():
    hist = cargar_historial()

    if not hist["pendientes"]:
        print("\n✔ No hay videos pendientes.")
        return None

    def ordenar(x):
        hora = x["publicar_en"]

        # Caso 1: formato simple "HH:MM"
        if len(hora) == 5 and hora[2] == ":":
            # Orden por hora del día
            return int(hora.replace(":", ""))

        # Caso 2: formato RFC3339 → convertir a datetime
        try:
            dt = datetime.strptime(hora, "%Y-%m-%dT%H:%M:%S-03:00")
            return dt.timestamp()
        except Exception:
            # fallback muy robusto
            return float("inf")

    hist["pendientes"].sort(key=ordenar)

    return hist["pendientes"][0]


# =====================================================
# 7. LÓGICA PRINCIPAL
# =====================================================
def subir_siguiente_video(privacidad="public"):
    hist = cargar_historial()
    siguiente = obtener_siguiente_video()

    if siguiente is None:
        return

    archivo = siguiente["archivo"]
    tipo = siguiente["tipo"]

    titulo_base = os.path.splitext(os.path.basename(archivo))[0]
    titulo = f"{titulo_base.replace('_', ' ').title()} — 1 minuto 🙏✨"

    descripcion = generar_descripcion(tipo, siguiente["publicar_en"], archivo)
    tags = generar_tags_from_descripcion(descripcion)

    publish_at = siguiente["publicar_en"]

    # Si hay publish_at → forzar modo scheduled
    modo_privacidad = privacidad
    
    video_id = subir_video_youtube(
        archivo,
        titulo,
        descripcion,
        tags,
        privacidad=modo_privacidad,
        publish_at=publish_at
    )

    hist_real = cargar_historial()

    hist_real["publicados"].append({
        **siguiente,
        "video_id": video_id,
        "fecha_publicado": datetime.now().isoformat()
    })

    hist_real["pendientes"] = [
        p for p in hist_real["pendientes"] if p["archivo"] != archivo
    ]

    guardar_historial(hist_real)
    mover_a_publicados(archivo, tipo)

    print("\n✔ Video procesado con éxito.\n")


# =====================================================
# 8. EJECUCIÓN MANUAL
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

    subir_siguiente_video(privacidad_forzada)
