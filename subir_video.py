import os
import json
import pickle
from datetime import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaFileUpload
import shutil
from openai import OpenAI
import random
import sys

from generar_descripcion import generar_descripcion, generar_tags_from_descripcion  # Importas tu función real



# -------- CONFIG --------
CLIENT_SECRETS_FILE = "client_secret.json"
TOKEN_FILE = "token.pickle"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
HISTORIAL = "historial.json"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def mover_a_publicados(ruta):
    base = os.path.basename(ruta)
    destino = os.path.join("videos/publicados", base)

    try:
        shutil.move(ruta, destino)
        print(f"📦 Video movido a: {destino}")
    except Exception as e:
        print(f"[ERROR] No se pudo mover el archivo a publicados: {e}")




# =====================================================
# 1. AUTENTICAR CON YOUTUBE
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
# 2. CARGAR Y GUARDAR HISTORIAL
# =====================================================
def cargar_historial():
    if not os.path.exists(HISTORIAL):
        return {"pendientes": [], "publicados": []}

    with open(HISTORIAL, "r") as f:
        content = f.read().strip()
        if not content:
            return {"pendientes": [], "publicados": []}

        data = json.loads(content)
        data.setdefault("pendientes", [])
        data.setdefault("publicados", [])
        return data


def guardar_historial(data):
    with open(HISTORIAL, "w") as f:
        json.dump(data, f, indent=4)


# =====================================================
# 3. SUBIR VIDEO A YOUTUBE
# =====================================================
def subir_video_youtube(ruta_video, titulo, descripcion, tags=None, privacidad="public"):
    youtube = obtener_servicio_youtube()

    request_body = {
        "snippet": {
            "title": titulo,
            "description": descripcion,
            "tags": tags or [
                "oracion diaria", "reflexion", "catolico",
                "biblia", "espiritualidad", "jesus",
                "dios", "evangelio", "minuto de oración"
            ],
            "categoryId": "22"  # People & Blogs
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

    print(f"\n📤 Subiendo video: {ruta_video}\n")

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Progreso: {int(status.progress() * 100)}%")

    print("\n🎉 VIDEO SUBIDO CON ÉXITO")
    print("➡ ID:", response.get("id"))

    return response.get("id")


# =====================================================
# 4. SELECCIONAR EL SIGUIENTE VIDEO A SUBIR
# =====================================================
def obtener_siguiente_video():
    hist = cargar_historial()

    if not hist["pendientes"]:
        print("\n✔ No hay videos pendientes para subir.")
        return None

    # ORDENAR POR HORA (05:00 → 12:00 → 19:00)
    ordenar_por_hora = lambda x: int(x["publicar_en"].replace(":", ""))
    hist["pendientes"].sort(key=ordenar_por_hora)

    siguiente = hist["pendientes"][0]
    return siguiente


# =====================================================
# 5. LÓGICA PRINCIPAL
# =====================================================
def subir_siguiente_video(privacidad="public"):
    hist = cargar_historial()
    siguiente = obtener_siguiente_video()
    if siguiente is None:
        return

    archivo = siguiente["archivo"]
    tipo = siguiente["tipo"]
    base = os.path.splitext(os.path.basename(archivo))[0]

    # Título profesional
    titulo = f"{base.replace('_', ' ').title()} — 1 minuto 🙏✨"

    descripcion = generar_descripcion(tipo, siguiente["publicar_en"], archivo)
    tags = generar_tags_from_descripcion(descripcion)

    # ======================================================
    # 📌 LEER LICENCIA DE LA MÚSICA Y AGREGARLA A LA DESCRIPCIÓN
    # ======================================================
    licencia_path = siguiente.get("licencia")

    licencia_txt = ""
    if licencia_path and os.path.exists(licencia_path):
        with open(licencia_path, "r", encoding="utf-8") as f:
            licencia_txt = f"\n\n{f.read().strip()}"
    else:
        print("[WARN] No se encontró licencia para esta música.")

    # Añadir la licencia al final de la descripción
    descripcion = descripcion + licencia_txt


    video_id = subir_video_youtube(
        archivo,
        titulo,
        descripcion,
        tags=tags,
        privacidad=privacidad
    )

    # MOVERLO A PUBLICADOS
    hist["publicados"].append({
        "archivo": archivo,
        "video_id": video_id,
        "fecha_publicado": datetime.now().isoformat(),
        "tipo": tipo
    })

    # ELIMINAR DE PENDIENTES
    hist["pendientes"] = hist["pendientes"][1:]

    guardar_historial(hist)

    mover_a_publicados(archivo)

    print("\n✔ Historial actualizado correctamente.\n")


# =====================================================
# EJECUCIÓN MANUAL O POR CRON
# =====================================================
if __name__ == "__main__":

    if "--privado" in sys.argv:
        privacidad_forzada = "private"
    elif "--oculto" in sys.argv:
        privacidad_forzada = "unlisted"
    else:
        privacidad_forzada = "public"
    
    
    subir_siguiente_video(privacidad_forzada)
