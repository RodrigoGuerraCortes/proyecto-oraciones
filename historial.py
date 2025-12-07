import json
import os
import traceback
from datetime import datetime

HISTORIAL = "historial.json"

# Estructura oficial del historial
ESTRUCTURA_HISTORIAL = {
    "pendientes": [],
    "publicados": [],
    "oraciones": [],
    "salmos": [],
    "imagenes": [],
    "musicas": []
}

print("\n[DEBUG] historial.py cargado correctamente\n")

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
        print(f"[DEBUG] BASE: {json.dumps(ESTRUCTURA_HISTORIAL, indent=4)}")
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
        for clave, valor in ESTRUCTURA_HISTORIAL.items():
            data.setdefault(clave, valor.copy())

        print("[DEBUG] cargar_historial() → contenido actual:")
        print(json.dumps(data, indent=4))
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

    # Detectar si está borrando listas importantes
    if len(data.get("imagenes", [])) == 0:
        print("⚠⚠⚠ [WARNING] Se está guardando IMAGENES = []")
    if len(data.get("musicas", [])) == 0:
        print("⚠⚠⚠ [WARNING] Se está guardando MUSICAS = []")

    print(json.dumps(data, indent=4))

    # asegurar consistencia
    final = {}
    for clave, valor in ESTRUCTURA_HISTORIAL.items():
        final[clave] = data.get(clave, valor.copy())

    print("\n[DEBUG] Datos que realmente se escriben en historial.json:")
    print(json.dumps(final, indent=4))

    with open(HISTORIAL, "w") as f:
        json.dump(final, f, indent=4)

    print("[DEBUG] historial.json guardado correctamente")
    print("===================================================================\n")


# --------------------------------------------------------
# Registrar uso (imagen, música, etc.)
# --------------------------------------------------------
def registrar_uso(tipo, nombre_archivo):
    print("===================================================================")
    print(f"[DEBUG] registrar_uso('{tipo}', '{nombre_archivo}') llamado desde → {quien_llamo()}")

    data = cargar_historial()
    hoy = datetime.now().isoformat()

    data.setdefault(tipo, [])
    data[tipo].append({
        "nombre": nombre_archivo,
        "fecha": hoy
    })

    print(f"[DEBUG] historial antes de guardar (tras registrar {tipo}):")
    print(json.dumps(data, indent=4))

    guardar_historial(data)

    print(f"[DEBUG] registrar_uso() completado para {tipo} → {nombre_archivo}")
    print("===================================================================\n")


# --------------------------------------------------------
# Registrar un video generado (pendiente de publicación)
# --------------------------------------------------------
def registrar_video_generado(archivo_video, tipo, musica, licencia, imagen, publicar_en):
    print("===================================================================")
    print(f"[DEBUG] registrar_video_generado() llamado desde → {quien_llamo()}")

    data = cargar_historial()

    entrada = {
        "archivo": archivo_video,
        "tipo": tipo,
        "musica": musica,
        "licencia": licencia,     # 🔥 SE MANTIENE SIEMPRE
        "imagen": imagen,         # 🔥 AÑADIDO
        "publicar_en": publicar_en,  # 🔥 AÑADIDO
        "fecha_generado": datetime.now().isoformat()
    }

    data.setdefault("pendientes", [])
    data["pendientes"].append(entrada)

    print("[DEBUG] Añadiendo a 'pendientes':")
    print(json.dumps(entrada, indent=4))

    guardar_historial(data)

    print("[DEBUG] registrar_video_generado() completado")
    print("===================================================================\n")
