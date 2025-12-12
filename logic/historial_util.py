# logic/historial_utils.py

import os
import json
from datetime import datetime

HISTORIAL = "historial.json"

PLATAFORMAS = ["youtube", "facebook", "instagram", "tiktok"]


# =====================================================
# 1. CARGAR / GUARDAR HISTORIAL
# =====================================================
def cargar_historial():
    """
    Carga el historial.json y garantiza que existan las claves
    'pendientes' y 'publicados'.
    """
    if not os.path.exists(HISTORIAL):
        return {"pendientes": [], "publicados": []}

    with open(HISTORIAL, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            # archivo vacío o corrupto
            return {"pendientes": [], "publicados": []}

    data.setdefault("pendientes", [])
    data.setdefault("publicados", [])
    return data


def guardar_historial(data):
    """Guarda historial.json de forma segura."""
    with open(HISTORIAL, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# =====================================================
# 2. ASEGURAR ESTRUCTURA DE PLATAFORMAS
# =====================================================
def asegurar_plataformas(video):
    """
    Garantiza que cada video pendiente tenga:

    "plataformas": {
        "youtube": {...},
        "facebook": {...},
        "instagram": {...},
        "tiktok": {...}
    }
    """
    if "plataformas" not in video:
        video["plataformas"] = {}

    for p in PLATAFORMAS:
        if p not in video["plataformas"]:
            video["plataformas"][p] = {
                "estado": "pendiente",
                "video_id": None,
                "fecha_publicado": None
            }

    return video


# =====================================================
# 3. OBTENER SIGUIENTE VIDEO PARA UNA PLATAFORMA
# =====================================================
def obtener_siguiente_video_para(plataforma):
    """
    Devuelve el siguiente video pendiente para esa plataforma,
    ordenado por fecha 'publicar_en'.
    """

    hist = cargar_historial()
    candidatos = []

    for item in hist["pendientes"]:
        item = asegurar_plataformas(item)

        estado = item["plataformas"][plataforma]["estado"]
        if estado == "pendiente":
            candidatos.append(item)

    if not candidatos:
        return None

    # ordenar por publicar_en
    def orden(x):
        try:
            dt = datetime.fromisoformat(x["publicar_en"])
            return dt.timestamp()
        except Exception:
            return float("inf")

    candidatos.sort(key=orden)
    return candidatos[0]


# =====================================================
# 4. MARCAR COMO PUBLICADO
# =====================================================
def marcar_como_publicado(plataforma, archivo, video_id):
    """
    Actualiza historial.json:
    - Cambia estado a 'publicado' para la plataforma
    - Guarda fecha actual
    - Guarda video_id retornado por la API
    """
    hist = cargar_historial()

    for item in hist["pendientes"]:
        if item["archivo"] == archivo:
            asegurar_plataformas(item)

            item["plataformas"][plataforma]["estado"] = "publicado"
            item["plataformas"][plataforma]["video_id"] = video_id
            item["plataformas"][plataforma]["fecha_publicado"] = datetime.now().isoformat()
            break

    guardar_historial(hist)


# =====================================================
# 5. CONVERTIR FECHA PARA PLATAFORMAS
# =====================================================
def convertir_fecha_para(plataforma, publicar_en):
    """
    YouTube → requiere RFC3339 (ya viene así desde generador)
    Facebook → requiere timestamp UNIX
    Instagram/TikTok → se definirá al integrarlos
    """

    if plataforma == "facebook":
        # convertir ISO → UNIX
        try:
            dt = datetime.fromisoformat(publicar_en)
            return int(dt.timestamp())
        except:
            # fallback: 20 minutos más
            return int(datetime.now().timestamp()) + 20*60

    # YouTube u otras plataformas pueden recibir ISO directamente
    return publicar_en
