import os
import sys
import json
import time
from datetime import datetime
import requests
from dotenv import load_dotenv

HISTORIAL = "historial.json"

load_dotenv()

FB_API_VERSION = os.getenv("FB_API_VERSION", "v24.0")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_USER_ACCESS_TOKEN = os.getenv("FB_USER_ACCESS_TOKEN")

if not FB_PAGE_ID or not FB_USER_ACCESS_TOKEN:
    print("[ERROR] Faltan variables de entorno FB_PAGE_ID o FB_USER_ACCESS_TOKEN")
    sys.exit(1)


# =====================================================
# 1. CARGAR / GUARDAR HISTORIAL
# =====================================================
def cargar_historial():
    if not os.path.exists(HISTORIAL):
        return {"pendientes": [], "publicados": []}

    with open(HISTORIAL, "r", encoding="utf-8") as f:
        contenido = f.read().strip()
        if not contenido:
            return {"pendientes": [], "publicados": []}

        data = json.loads(contenido)
        data.setdefault("pendientes", [])
        data.setdefault("publicados", [])
        return data


def guardar_historial(data):
    with open(HISTORIAL, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# =====================================================
# 2. CONVERTIR publicar_en → scheduled_publish_time (UNIX)
# =====================================================
def iso_to_unix(iso_str):
    """
    Recibe algo tipo 2025-12-11T23:10:00-03:00
    y lo convierte a timestamp Unix (segundos).
    """
    try:
        # Quitamos el offset -03:00 para usar fromisoformat
        # Python lo soporta directamente
        dt = datetime.fromisoformat(iso_str)
        return int(dt.timestamp())
    except Exception as e:
        print(f"[WARN] No se pudo parsear '{iso_str}' como ISO: {e}")
        # Si falla, programa para dentro de 20 minutos
        return int(time.time()) + 20 * 60


# =====================================================
# 3. OBTENER SIGUIENTE VIDEO PARA FACEBOOK
# =====================================================
def obtener_siguiente_video_facebook():
    hist = cargar_historial()

    candidatos = []
    for item in hist.get("pendientes", []):
        plataformas = item.get("plataformas") or {}
        fb = plataformas.get("facebook") or {}

        if fb.get("estado") == "pendiente":
            candidatos.append(item)

    if not candidatos:
        print("✔ No hay videos pendientes para Facebook.")
        return None

    # Ordenamos por publicar_en (igual que en YouTube)
    def ordenar(x):
        hora = x.get("publicar_en", "")
        try:
            dt = datetime.fromisoformat(hora)
            return dt.timestamp()
        except Exception:
            return float("inf")

    candidatos.sort(key=ordenar)
    return candidatos[0]


# =====================================================
# 4. SUBIR EL ARCHIVO COMO REEL (upload_phase=start/finish)
# =====================================================
def subir_reel_facebook(ruta_video, descripcion, scheduled_publish_time):
    """
    Sigue la guía de Reels:
      1) POST /{page-id}/video_reels?upload_phase=start
      2) POST binary con 'file' y upload_phase=finish
      3) publish con video_state=SCHEDULED y scheduled_publish_time
    """

    base_url = f"https://graph.facebook.com/{FB_API_VERSION}"

    # 1. Inicializar sesión de subida
    init_url = f"{base_url}/{FB_PAGE_ID}/video_reels"
    init_params = {
        "access_token": FB_USER_ACCESS_TOKEN,
        "upload_phase": "start",
    }
    print("🟡 Inicializando sesión de subida...")
    r = requests.post(init_url, params=init_params)
    r.raise_for_status()
    data = r.json()
    upload_url = data.get("upload_url")
    video_id = data.get("video_id")

    if not upload_url or not video_id:
        raise RuntimeError(f"Respuesta inesperada en init: {data}")

    print(f"✅ Sesión iniciada. video_id={video_id}")

    # 2. Subir el archivo binario con upload_phase=finish
    print("🟡 Subiendo archivo de video...")
    with open(ruta_video, "rb") as f:
        files = {
            "file": f
        }
        params_finish = {
            "access_token": FB_USER_ACCESS_TOKEN,
            "upload_phase": "finish"
        }
        r2 = requests.post(upload_url, params=params_finish, files=files)
        r2.raise_for_status()
        data_finish = r2.json()
        print("✅ Subida completada:", data_finish)

    # 3. Publicar el Reel (programado)
    publish_url = f"{base_url}/{FB_PAGE_ID}/video_reels"
    publish_params = {
        "access_token": FB_USER_ACCESS_TOKEN,
        "video_id": video_id,
        "upload_phase": "finish",  # algunos ejemplos lo incluyen
        "video_state": "SCHEDULED",
        "description": descripcion,
        "scheduled_publish_time": scheduled_publish_time,
    }

    print("🟡 Enviando petición de publicación programada...")
    r3 = requests.post(publish_url, params=publish_params)
    r3.raise_for_status()
    data_publish = r3.json()
    print("✅ Publicación programada respuesta:", data_publish)

    # La doc indica que al final devuelve {"success": true}
    if not data_publish.get("success"):
        raise RuntimeError(f"No se pudo programar el Reel correctamente: {data_publish}")

    return video_id


# =====================================================
# 5. LÓGICA PRINCIPAL
# =====================================================
def subir_siguiente_video_facebook():
    hist = cargar_historial()
    siguiente = obtener_siguiente_video_facebook()

    if siguiente is None:
        return

    archivo = siguiente["archivo"]
    tipo = siguiente.get("tipo", "oracion")
    publicar_en = siguiente.get("publicar_en")

    # Título tipo "Oracion Por Los Matrimonios..." (igual que en YouTube)
    titulo_base = os.path.splitext(os.path.basename(archivo))[0]
    titulo = f"{titulo_base.replace('_', ' ').title()} — 1 minuto 🙏✨"

    # Para Facebook: descripción sencilla con título y quizá algunos hashtags genéricos
    descripcion = f"{titulo}\n\n#oracion #jesus #catolico"

    # Programar según publicar_en
    scheduled_publish_time = iso_to_unix(publicar_en)

    print(f"\n📤 Subiendo Reel para Facebook:")
    print(f"   Archivo: {archivo}")
    print(f"   Publicar en: {publicar_en} (unix={scheduled_publish_time})")

    video_id = subir_reel_facebook(
        ruta_video=archivo,
        descripcion=descripcion,
        scheduled_publish_time=scheduled_publish_time,
    )

    # Actualizar historial
    hist_real = cargar_historial()

    for item in hist_real.get("pendientes", []):
        if item["archivo"] == archivo:
            # Asegurarse de que exista la estructura plataformas
            plataformas = item.setdefault("plataformas", {})
            fb = plataformas.setdefault("facebook", {
                "estado": "pendiente",
                "video_id": None,
                "fecha_publicado": None,
            })

            fb["estado"] = "publicado"
            fb["video_id"] = video_id
            fb["fecha_publicado"] = datetime.now().isoformat()
            break

    guardar_historial(hist_real)

    print("\n✔ Reel programado en Facebook correctamente.\n")


# =====================================================
# 6. ENTRY POINT
# =====================================================
if __name__ == "__main__":
    subir_siguiente_video_facebook()
