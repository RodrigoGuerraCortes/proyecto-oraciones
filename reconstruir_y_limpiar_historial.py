import json
import shutil
from datetime import datetime

RUTA = "historial.json"
BACKUP = "historial_backup.json"

# Lista de músicas con licencia real
MUSICAS_CON_LICENCIA = {
    "10.mp3": "musica/licence/licence_10.txt"
}


def cargar():
    with open(RUTA, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar(data):
    with open(RUTA, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def parse_fecha(f):
    try:
        return datetime.fromisoformat(f)
    except:
        return None


def encontrar_par_imagen_musica(imagenes, musicas, fecha_objetivo, ventana_segundos=3):
    fecha_obj = parse_fecha(fecha_objetivo)
    if not fecha_obj:
        return None, None

    mejor_img = None
    mejor_mus = None
    mejor_diff = None

    for img in imagenes:
        f_img = parse_fecha(img["fecha"])
        if not f_img:
            continue

        for mus in musicas:
            f_mus = parse_fecha(mus["fecha"])
            if not f_mus:
                continue

            diff = abs((f_img - f_mus).total_seconds())

            if diff > ventana_segundos:
                continue

            if mejor_diff is None or diff < mejor_diff:
                mejor_diff = diff
                mejor_img = img["nombre"]
                mejor_mus = mus["nombre"]

    return mejor_img, mejor_mus


def asignar_licencia_si_corresponde(pub, musica):
    if musica in MUSICAS_CON_LICENCIA:
        pub["licencia"] = MUSICAS_CON_LICENCIA[musica]
    else:
        pub["licencia"] = None


def reconstruir_historial():
    print("⬆️ Creando respaldo del historial...")
    shutil.copy(RUTA, BACKUP)

    data = cargar()
    imagenes = data.get("imagenes", [])
    musicas = data.get("musicas", [])

    print("🔧 Reconstruyendo datos de videos antiguos...")

    for pub in data.get("publicados", []):
        fecha_gen = pub.get("fecha_generado")
        if not fecha_gen:
            continue

        img, mus = encontrar_par_imagen_musica(imagenes, musicas, fecha_gen)

        if img:
            pub["imagen"] = img

        if mus:
            pub["musica"] = mus
            asignar_licencia_si_corresponde(pub, mus)

    print("✔ Reconstrucción completada correctamente.")

    # Eliminar listas antiguas
    for k in ["imagenes", "musicas", "oraciones", "salmos"]:
        if k in data:
            del data[k]

    guardar(data)
    print("✨ Historial final guardado y optimizado.")


if __name__ == "__main__":
    reconstruir_historial()
