import json
import os
import traceback
from datetime import datetime
import hashlib

HISTORIAL = "historial.json"

# Estructura oficial del historial
ESTRUCTURA_HISTORIAL = {
    "pendientes": [],
    "publicados": [],
    "textos_usados": {
        "textos/oraciones": [],
        "textos/salmos": []
    }
}

print("\n[DEBUG] historial.py cargado correctamente\n")


def tag_ya_existe(tag):
    hist = cargar_historial()
    usados = set()

    for pub in hist.get("publicados", []):
        usados.add(pub.get("tag"))

    for pen in hist.get("pendientes", []):
        usados.add(pen.get("tag"))

    return tag in usados


# --------------------------------------------------------
# Utilidad para detectar QUIÉN llamó a la función
# --------------------------------------------------------
def quien_llamo():
    stack = traceback.extract_stack()
    # ignorar últimas 2 líneas (esta función + wrapper)
    caller = stack[-3]
    return f"{caller.filename}:{caller.lineno} ({caller.name})"


# --------------------------------------------------------
# Cargar historial
# --------------------------------------------------------
def cargar_historial():
    print("===================================================================")
    print(f"[DEBUG] cargar_historial() llamado desde → {quien_llamo()}")

    if not os.path.exists(HISTORIAL):
        print("[DEBUG] historial.json NO existe, devolviendo estructura base")
        print("===================================================================\n")
        return ESTRUCTURA_HISTORIAL.copy()

    try:
        with open(HISTORIAL, "r") as f:
            contenido = f.read().strip()

        if not contenido:
            print("[DEBUG] historial.json vacío → usando estructura base")
            print("===================================================================\n")
            return ESTRUCTURA_HISTORIAL.copy()

        data = json.loads(contenido)

        # asegurar todas las claves
        # asegurar todas las claves
        for clave, valor in ESTRUCTURA_HISTORIAL.items():
            data.setdefault(clave, valor.copy() if isinstance(valor, list) else valor.copy())

        # ------------------------------------------------------
        # 🔥 Parche: asegurar que textos_usados existe siempre
        # ------------------------------------------------------
        if "textos_usados" not in data:
            data["textos_usados"] = {
                "textos/oraciones": [],
                "textos/salmos": []
            }

        if "textos/oraciones" not in data["textos_usados"]:
            data["textos_usados"]["textos/oraciones"] = []

        if "textos/salmos" not in data["textos_usados"]:
            data["textos_usados"]["textos/salmos"] = []


        # 🔁 Compatibilidad hacia atrás:
        # si un publicado tiene "tag" pero no "tag_legacy", lo copiamos
        for pub in data.get("publicados", []):
            if "tag" in pub and "tag_legacy" not in pub:
                pub["tag_legacy"] = pub["tag"]

        #print("[DEBUG] cargar_historial() → contenido actual (normalizado):")
        #print(json.dumps(data, indent=4))
        print("===================================================================\n")
        return data

    except Exception as e:
        print(f"[ERROR] cargar_historial falló: {e}")
        print("[DEBUG] Usando estructura base por seguridad")
        print("===================================================================\n")
        return ESTRUCTURA_HISTORIAL.copy()


# --------------------------------------------------------
# Guardar historial
# --------------------------------------------------------
def guardar_historial(data):
    print("===================================================================")
    print(f"[DEBUG] guardar_historial() llamado desde → {quien_llamo()}")
    print("[DEBUG] Datos a guardar:")

    # asegurar consistencia
    final = {}
    for clave, valor in ESTRUCTURA_HISTORIAL.items():
        final[clave] = data.get(clave, valor.copy())

    with open(HISTORIAL, "w") as f:
        json.dump(final, f, indent=4)

    print("[DEBUG] historial.json guardado correctamente")
    print("===================================================================\n")




# --------------------------------------------------------
# Registrar un video generado (pendiente de publicación)
# --------------------------------------------------------
def registrar_video_generado(
    archivo_video,
    tipo,
    musica,
    licencia,
    imagen,
    publicar_en,
    tag=None,
    tag_legacy=None
):
    """
    Registra un video en la cola de 'pendientes'.

    - tag:        nuevo TAG "inteligente" (tipo + contenido + imagen + música)
    - tag_legacy: TAG antiguo (nombre_archivo + imagen + música) para compatibilidad
    """

    print("===================================================================")
    print(f"[DEBUG] registrar_video_generado() llamado")

    data = cargar_historial()

    # Nombre base del archivo (sin extensión)
    texto_base = os.path.splitext(os.path.basename(archivo_video))[0]

    # TAG legacy (esquema antiguo) si no viene definido
    if tag_legacy is None:
        base_tag_legacy = f"{texto_base}|{imagen}|{musica}"
        tag_legacy = hashlib.sha256(base_tag_legacy.encode()).hexdigest()[:12]

    # Si no se pasó TAG nuevo, por compatibilidad usamos el legacy
    if tag is None:
        tag = tag_legacy

    entrada = {
        "archivo": archivo_video,
        "tipo": tipo,
        "musica": musica,
        "licencia": licencia,
        "imagen": imagen,
        "publicar_en": publicar_en,
        "fecha_generado": datetime.now().isoformat(),
        "tag": tag,
        "tag_legacy": tag_legacy
    }

    data.setdefault("pendientes", [])
    data["pendientes"].append(entrada)

    guardar_historial(data)

    print(f"[DEBUG] registrar_video_generado() completado")
    print(f"[DEBUG] TAG nuevo:    {tag}")
    print(f"[DEBUG] TAG legacy:  {tag_legacy}")
    print("===================================================================\n")
