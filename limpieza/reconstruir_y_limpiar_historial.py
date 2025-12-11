import json
import shutil
from datetime import datetime
import hashlib

RUTA = "historial.json"
BACKUP = "historial_backup.json"

# Licencias disponibles por música
MUSICA_LICENCIA = {
    "9.mp3": "musica/licence/licence_9.txt",
    "8.mp3": "musica/licence/licence_8.txt",
    "6.mp3": "musica/licence/licence_6.txt",
    "2.mp3": "musica/licence/licence_2.txt",
    "10.mp3": "musica/licence/licence_10.txt",
    "amen-i-cathedral-polish-aramaic-religious-music-chorus-433992.mp3":
        "musica/licence/licence_amen-i-cathedral-polish-aramaic-religious-music-chorus-433992.txt",
    "christian-439968.mp3":
        "musica/licence/licence_christian-439968.txt",
}

def parse_fecha(f):
    try:
        return datetime.fromisoformat(f)
    except:
        return None

def generar_tag(texto, imagen, musica):
    base = f"{texto}|{imagen}|{musica}"
    return hashlib.sha256(base.encode()).hexdigest()[:12]

def extraer_texto(path):
    return path.split("/")[-1].replace(".mp4", "")

def encontrar_cercano(fecha_objetivo, lista, tolerancia_seg):
    """
    Busca el archivo cuya fecha esté más cerca de fecha_objetivo
    dentro de una tolerancia en segundos.
    Devuelve el nombre del archivo si lo encuentra.
    """
    fecha_base = parse_fecha(fecha_objetivo)
    if not fecha_base:
        return None

    mejor_nombre = None
    mejor_diff = None

    for item in lista:
        f = parse_fecha(item["fecha"])
        if not f:
            continue

        diff = abs((f - fecha_base).total_seconds())

        if diff <= tolerancia_seg:
            if mejor_diff is None or diff < mejor_diff:
                mejor_diff = diff
                mejor_nombre = item["nombre"]

    return mejor_nombre


def reconstruir():
    # Backup
    shutil.copy(RUTA, BACKUP)
    print("📀 Backup creado en:", BACKUP)

    # Cargar historial
    with open(RUTA, "r", encoding="utf-8") as f:
        data = json.load(f)

    publicados = data["publicados"]
    imagenes = data["imagenes"]
    musicas = data["musicas"]

    # Encontrar índice desde donde empezar
    try:
        idx = next(i for i, v in enumerate(publicados)
                   if v["archivo"].endswith("oracion_del_enfermo.mp4"))
    except StopIteration:
        print("❌ No se encontró 'oracion_del_enfermo.mp4'. Abortado.")
        return

    print(f"➡ Reconstruyendo desde índice {idx} (oracion_del_enfermo en adelante)")

    corregidos = 0

    for v in publicados[idx:]:
        fecha = v.get("fecha_generado")
        if not fecha:
            # Si no tiene fecha_generado NO SE TOCA
            continue

        tipo = v["tipo"]

        # Tolerancia: 10s para oraciones, 10min para salmos
        tolerancia = 10 if tipo == "oracion" else 600

        # --------------------------
        #    RECONSTRUIR IMAGEN
        # --------------------------
        if v.get("imagen") in (None, "", "aleatoria"):
            img = encontrar_cercano(fecha, imagenes, tolerancia)
            if img:
                v["imagen"] = img

        # --------------------------
        #    RECONSTRUIR MÚSICA
        # --------------------------
        if not v.get("musica"):
            mus = encontrar_cercano(fecha, musicas, tolerancia)
            if mus:
                v["musica"] = mus
                v["licencia"] = MUSICA_LICENCIA.get(mus)

        # --------------------------
        #    GENERAR TAG
        # --------------------------
        img_final = v.get("imagen")
        mus_final = v.get("musica")

        if img_final not in (None, "", "aleatoria") and mus_final:
            texto = extraer_texto(v["archivo"])
            v["tag"] = generar_tag(texto, img_final, mus_final)
            corregidos += 1

    # Guardar cambios
    with open(RUTA, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"✔ Reconstrucción completada. Videos corregidos: {corregidos}")


if __name__ == "__main__":
    reconstruir()
