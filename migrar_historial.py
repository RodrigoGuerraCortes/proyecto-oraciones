import json
import os
import re
from datetime import datetime
from generar_video_v2 import generar_tag_inteligente

HISTORIAL_ORIG = "historial.json"
HISTORIAL_MIGRADO = "historial_migrado.json"


# ============================================
#   UTILIDAD → Limpia nombres
# ============================================
def normalize(s):
    return s.lower().replace(".mp4", "").replace(".txt", "").strip()


# ============================================
#   BUSCAR TEXTO DE ORACIÓN
# ============================================
def buscar_texto_oracion(base):
    carpeta = "textos/oraciones"

    candidates = [
        f"{carpeta}/{base}.txt",
        f"{carpeta}/oracion_{base}.txt"
    ]

    # Caso base = "oracion_acto_de_fe"
    if base.startswith("oracion_"):
        b2 = base.replace("oracion_", "")
        candidates.append(f"{carpeta}/{b2}.txt")

    # Búsqueda directa
    for c in candidates:
        if os.path.exists(c):
            return c, normalize(os.path.basename(c))

    # Buscar por substring
    for fname in os.listdir(carpeta):
        if base in fname.lower():
            return f"{carpeta}/{fname}", normalize(fname)

    # Buscar por prefijo
    for fname in os.listdir(carpeta):
        if fname.lower().startswith(base[:10]):
            return f"{carpeta}/{fname}", normalize(fname)

    return None, None


# ============================================
#   BUSCAR TEXTO DE SALMO
# ============================================
def extraer_numero_salmo(base):
    match = re.search(r"salmo[_\-]?(\d+)", base.lower())
    return match.group(1) if match else None


def buscar_texto_salmo(base):
    carpeta = "textos/salmos"

    # Intento directo
    path1 = f"{carpeta}/{base}.txt"
    if os.path.exists(path1):
        return path1, normalize(base)

    # Encontrar número del salmo
    num = extraer_numero_salmo(base)
    if num:
        # buscar archivo que contenga "salmo_XX"
        for fname in os.listdir(carpeta):
            if f"salmo_{num}" in fname.lower():
                return f"{carpeta}/{fname}", normalize(fname)

    # Buscar por substring del nombre
    for fname in os.listdir(carpeta):
        if base in fname.lower():
            return f"{carpeta}/{fname}", normalize(fname)

    # Buscar por prefijo
    for fname in os.listdir(carpeta):
        if fname.lower().startswith(base[:10]):
            return f"{carpeta}/{fname}", normalize(fname)

    return None, None


# ============================================
#   ESTIMAR DURACIÓN SI NO TENEMOS DATA REAL
# ============================================
def estimar_duracion(texto):
    lineas = [l for l in texto.splitlines() if l.strip()]
    n = len(lineas)
    if n <= 7:
        return 20
    elif n <= 12:
        return 28
    else:
        return 35


# ============================================
#   MAIN MIGRATION
# ============================================
def main():
    with open(HISTORIAL_ORIG, "r") as f:
        data = json.load(f)

    publicados = data.get("publicados", [])

    textos_usados = {
        "textos/oraciones": [],
        "textos/salmos": []
    }

    for pub in publicados:
        archivo_video = pub["archivo"]
        tipo = pub["tipo"]
        fecha = pub["fecha_generado"]
        imagen = pub.get("imagen", "desconocida")
        musica = pub.get("musica", "desconocida")

        base = normalize(os.path.basename(archivo_video))

        # Buscar texto real
        if tipo == "oracion":
            txt_path, txt_name = buscar_texto_oracion(base)
            folder_key = "textos/oraciones"
        else:
            txt_path, txt_name = buscar_texto_salmo(base)
            folder_key = "textos/salmos"

        if not txt_path:
            print(f"[WARN] No se encontró archivo TXT para {archivo_video}")
            continue

        # Registrar texto usado
        textos_usados[folder_key].append({
            "nombre": txt_name,
            "fecha": fecha
        })

        # Leer contenido del texto
        with open(txt_path, "r", encoding="utf-8") as tf:
            texto = tf.read()

        # Calcular duración aproximada
        dur = estimar_duracion(texto)

        # Generar nuevo TAG
        new_tag = generar_tag_inteligente(
            tipo=tipo,
            texto=texto,
            imagen=imagen,
            musica=musica,
            duracion=dur
        )

        pub["tag"] = new_tag
        pub["tag_legacy"] = new_tag

    # Integrar textos usados
    data["textos_usados"] = textos_usados

    with open(HISTORIAL_MIGRADO, "w") as f:
        json.dump(data, f, indent=4)

    print("Migración completada exitosamente.")
    print("Archivo generado:", HISTORIAL_MIGRADO)


if __name__ == "__main__":
    main()
