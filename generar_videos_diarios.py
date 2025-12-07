import json
import os
from datetime import datetime
import subprocess
import sys
from historial import cargar_historial, guardar_historial

PYTHON = sys.executable  # usa el python actual

MODO_TEST = False
if len(sys.argv) > 1 and sys.argv[1] == "test":
    MODO_TEST = True
    print("⚠ MODO TEST ACTIVADO (10s)")

# --------------------------------------------------------------------
# Asegurar que las carpetas existen
# --------------------------------------------------------------------
def asegurar_carpetas():
    for c in ["videos/oraciones", "videos/salmos"]:
        os.makedirs(c, exist_ok=True)

# --------------------------------------------------------------------
# Obtener el archivo mp4 más reciente
# --------------------------------------------------------------------
def ultimo_archivo_generado(carpeta):
    archivos = [
        os.path.join(carpeta, f)
        for f in os.listdir(carpeta)
        if f.endswith(".mp4")
    ]

    if not archivos:
        return None

    archivos.sort(key=lambda x: os.path.getmtime(x))
    return archivos[-1]

# --------------------------------------------------------------------
# Extraer metadata si está disponible
# --------------------------------------------------------------------
def extraer_metadata_video(ruta):
    """
    Busca en historial la entrada que coincide con el archivo generado.
    Así obtenemos imagen, música y licencia REAL.
    """
    historial = cargar_historial()

    for p in historial.get("pendientes", []):
        if p["archivo"] == ruta:
            return {
                "imagen": p.get("imagen", "aleatoria"),
                "musica": p.get("musica", None),
                "licencia": p.get("licencia", None)
            }

    return {
        "imagen": "aleatoria",
        "musica": None,
        "licencia": None
    }

# --------------------------------------------------------------------
# Generar los 3 videos diarios
# --------------------------------------------------------------------
def generar_videos_diarios():
    asegurar_carpetas()

    print("\n==============================")
    print(" GENERANDO VIDEOS DEL DÍA")
    print("==============================\n")

    historial = cargar_historial()

    # 🔥 Lista donde agregaremos los videos generados en esta ejecución
    nuevos_pendientes = []

    # ======================================================
    # 1) ORACIÓN DE LA MAÑANA
    # ======================================================
    print("\n📌 Generando Oración de la mañana...\n")
    cmd = [PYTHON, "generar_video.py", "1", "oracion"]
    if MODO_TEST: cmd.append("test")
    subprocess.run(cmd)

    ult = ultimo_archivo_generado("videos/oraciones")
    meta = extraer_metadata_video(ult)

    nuevos_pendientes.append({
        "archivo": ult,
        "tipo": "oracion",
        "imagen": meta["imagen"],
        "musica": meta["musica"],
        "licencia": meta["licencia"],
        "publicar_en": "10:00",
        "fecha_generado": datetime.now().isoformat()
    })

    # ======================================================
    # 2) SALMO DEL DÍA
    # ======================================================
    print("\n📌 Generando Salmo del día...\n")
    cmd = [PYTHON, "generar_video.py", "1", "salmo"]
    if MODO_TEST: cmd.append("test")
    subprocess.run(cmd)

    ult = ultimo_archivo_generado("videos/salmos")
    meta = extraer_metadata_video(ult)

    nuevos_pendientes.append({
        "archivo": ult,
        "tipo": "salmo",
        "imagen": meta["imagen"],
        "musica": meta["musica"],
        "licencia": meta["licencia"],
        "publicar_en": "15:30",
        "fecha_generado": datetime.now().isoformat()
    })

    # ======================================================
    # 3) ORACIÓN DE LA NOCHE
    # ======================================================
    print("\n📌 Generando Oración de la noche...\n")
    cmd = [PYTHON, "generar_video.py", "1", "oracion"]
    if MODO_TEST: cmd.append("test")
    subprocess.run(cmd)

    ult = ultimo_archivo_generado("videos/oraciones")
    meta = extraer_metadata_video(ult)

    nuevos_pendientes.append({
        "archivo": ult,
        "tipo": "oracion",
        "imagen": meta["imagen"],
        "musica": meta["musica"],
        "licencia": meta["licencia"],
        "publicar_en": "23:10",
        "fecha_generado": datetime.now().isoformat()
    })

    # ======================================================
    # 🔥 Guardar historial sin tocar imágenes/músicas globales
    # ======================================================
    hist_real = cargar_historial()
    hist_real["pendientes"].extend(nuevos_pendientes)
    guardar_historial(hist_real)

    print("\n==============================")
    print(" ✔ VIDEOS GENERADOS Y REGISTRADOS")
    print("==============================\n")

# Entry point
if __name__ == "__main__":
    generar_videos_diarios()
