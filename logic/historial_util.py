import os
import json
import shutil
from datetime import datetime

HISTORIAL = "historial.json"
PLATAFORMAS = ["youtube", "facebook", "instagram", "tiktok"]

def marcar_como_procesando(plataforma, archivo):
    hist = cargar_historial()

    for item in hist["pendientes"]:
        if item["archivo"] == archivo:
            item["plataformas"][plataforma]["estado"] = "procesando"
            item["plataformas"][plataforma]["fecha_publicado"] = None
            guardar_historial(hist)
            return

    guardar_historial(hist)


def marcar_como_pendiente(plataforma, archivo):
    hist = cargar_historial()

    for item in hist["pendientes"]:
        if item["archivo"] == archivo:
            item["plataformas"][plataforma]["estado"] = "pendiente"
            item["plataformas"][plataforma]["video_id"] = None
            item["plataformas"][plataforma]["fecha_publicado"] = None
            guardar_historial(hist)
            return

    guardar_historial(hist)
    

# =====================================================
# 1. CARGAR / GUARDAR HISTORIAL
# =====================================================
def cargar_historial():
    if not os.path.exists(HISTORIAL):
        return {"pendientes": [], "publicados": []}

    try:
        with open(HISTORIAL, "r", encoding="utf-8") as f:
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
# 2. ASEGURAR ESTRUCTURA Y PERSISTIR
# =====================================================
def asegurar_plataformas(video):
    """
    Garantiza que el video tenga la estructura correcta en 'plataformas'
    y persiste el cambio automáticamente en historial.json.
    """

    hist = cargar_historial()

    for item in hist["pendientes"]:
        if item["archivo"] == video["archivo"]:
            # asegurar estructura en memoria
            if "plataformas" not in item:
                item["plataformas"] = {}

            for p in PLATAFORMAS:
                if p not in item["plataformas"]:
                    item["plataformas"][p] = {
                        "estado": "pendiente",
                        "video_id": None,
                        "fecha_publicado": None
                    }

            guardar_historial(hist)
            return item  # devolvemos el video ya actualizado

    return video  # fallback (no debería ocurrir)


# =====================================================
# 3. OBTENER SIGUIENTE VIDEO PARA UNA PLATAFORMA
# =====================================================
def obtener_siguiente_video_para(plataforma):
    hist = cargar_historial()
    candidatos = []

    for item in hist["pendientes"]:
        item = asegurar_plataformas(item)

        if item["plataformas"][plataforma]["estado"] == "pendiente":
            candidatos.append(item)

    if not candidatos:
        return None

    def orden(v):
        try:
            return datetime.fromisoformat(v["publicar_en"]).timestamp()
        except:
            return float("inf")

    candidatos.sort(key=orden)
    return candidatos[0]


# =====================================================
# 4. MARCAR COMO PUBLICADO
# =====================================================
def marcar_como_publicado(plataforma, archivo, video_id):
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
# 5. MOVER ARCHIVO FÍSICO
# =====================================================
def mover_archivo(video):
    archivo = video["archivo"]
    tipo = video.get("tipo", "otros")

    base = os.path.basename(archivo)
    destino_dir = os.path.join("videos", "publicados", tipo + "s")
    os.makedirs(destino_dir, exist_ok=True)

    destino = os.path.join(destino_dir, base)

    shutil.move(archivo, destino)
    video["archivo"] = destino

# =====================================================
# 6. MOVER A PUBLICADOS EN HISTORIAL
# =====================================================
def mover_a_publicados(video):
    hist = cargar_historial()

    # buscar el objeto real
    real = next((v for v in hist["pendientes"] if v["archivo"] == video["archivo"]), None)
    if not real:
        return

    hist["pendientes"].remove(real)
    hist["publicados"].append(real)

    guardar_historial(hist)

    try:
        if os.path.exists(real["archivo"]):
            mover_archivo(real)
    except Exception as e:
        print(f"⚠ Error moviendo archivo físico: {e}")

# =====================================================
# 7. CONVERTIR FECHA PARA PLATAFORMAS
# =====================================================
def convertir_fecha_para(plataforma, publicar_en):
    if plataforma == "facebook":
        try:
            dt = datetime.fromisoformat(publicar_en)
            return int(dt.timestamp())
        except:
            return int(datetime.now().timestamp()) + 20 * 60
    if plataforma == "instagram":
        try:
            dt = datetime.fromisoformat(publicar_en)
            return int(dt.timestamp())
        except:
            return int(datetime.now().timestamp() + 600)

    return publicar_en  # YouTube usa ISO
