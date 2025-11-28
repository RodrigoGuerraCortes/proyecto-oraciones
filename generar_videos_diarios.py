import json
import os
from datetime import datetime
import subprocess
import sys

HISTORIAL = "historial.json"

PYTHON = sys.executable  # usa el python que ejecutó este script


MODO_TEST = False
if len(sys.argv) > 1 and sys.argv[1] == "test":
    MODO_TEST = True
    print("⚠ MODO TEST ACTIVADO: videos de 10 segundos")



def ultimo_archivo_generado(carpeta):
    archivos = [
        os.path.join(carpeta, f)
        for f in os.listdir(carpeta)
        if f.endswith(".mp4")
    ]

    if not archivos:
        return None

    # Ordenar por fecha de modificación real
    archivos.sort(key=lambda x: os.path.getmtime(x))

    return archivos[-1]

# ------------------------------
# Cargar historial extendido
# ------------------------------
def cargar_historial():
    if not os.path.exists(HISTORIAL):
        return {
            "pendientes": [],
            "publicados": [],
            "oraciones": [],
            "salmos": []
        }
    try:
        with open(HISTORIAL, "r") as f:
            contenido = f.read().strip()
            if not contenido:
                return {
                    "pendientes": [],
                    "publicados": [],
                    "oraciones": [],
                    "salmos": []
                }
            data = json.loads(contenido)

            # asegurar claves nuevas
            data.setdefault("pendientes", [])
            data.setdefault("publicados", [])
            data.setdefault("oraciones", [])
            data.setdefault("salmos", [])
            return data
    except:
        return {
            "pendientes": [],
            "publicados": [],
            "oraciones": [],
            "salmos": []
        }

# ------------------------------
# Guardar historial extendido
# ------------------------------
def guardar_historial(data):
    with open(HISTORIAL, "w") as f:
        json.dump(data, f, indent=4)


# ------------------------------
# Crear los 3 videos diarios
# ------------------------------
def generar_videos_diarios():
    print("\n==============================")
    print(" GENERANDO VIDEOS DEL DÍA")
    print("==============================\n")

    historial = cargar_historial()

    # -------------------------------------------------------------------
    # 1) ORACIÓN DE LA MAÑANA
    # -------------------------------------------------------------------
    print("\n📌 Generando Oración de la mañana...\n")
    cmd = [PYTHON, "generar_video.py", "1", "oracion"]
    if MODO_TEST:
        cmd.append("test")
    subprocess.run(cmd)

    # Obtener el último generado (carpeta videos/oraciones/)
    ult_oracion = ultimo_archivo_generado("videos/oraciones")

    historial["pendientes"].append({
        "archivo": ult_oracion,
        "tipo": "oracion",
        "publicar_en": "05:00",
        "fecha_generado": datetime.now().isoformat()
    })

    # -------------------------------------------------------------------
    # 2) SALMO DEL DÍA
    # -------------------------------------------------------------------
    print("\n📌 Generando Salmo del día...\n")
    cmd = [PYTHON, "generar_video.py", "1", "salmo"]
    if MODO_TEST:
        cmd.append("test")
    subprocess.run(cmd)



    ult_salmo = ultimo_archivo_generado("videos/salmos")


    historial["pendientes"].append({
        "archivo": ult_salmo,
        "tipo": "salmo",
        "publicar_en": "12:00",
        "fecha_generado": datetime.now().isoformat()
    })

    # -------------------------------------------------------------------
    # 3) ORACIÓN DE LA NOCHE
    # -------------------------------------------------------------------
    print("\n📌 Generando Oración de la noche...\n")
    cmd = [PYTHON, "generar_video.py", "1", "oracion"]
    if MODO_TEST:
        cmd.append("test")
    subprocess.run(cmd)

    ult_oracion2 = ultimo_archivo_generado("videos/oraciones")
    

    historial["pendientes"].append({
        "archivo": ult_oracion2,
        "tipo": "oracion",
        "publicar_en": "19:00",
        "fecha_generado": datetime.now().isoformat()
    })

    guardar_historial(historial)

 

    print("\n==============================")
    print(" ✔ VIDEOS GENERADOS Y REGISTRADOS")
    print("==============================\n")


# Entry point
if __name__ == "__main__":
    generar_videos_diarios()
