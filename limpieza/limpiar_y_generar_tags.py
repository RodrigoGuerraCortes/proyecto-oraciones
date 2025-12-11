import json
import hashlib
import shutil
import os

RUTA = "historial.json"
BACKUP = "historial_backup_final.json"


def generar_tag(texto, imagen, musica):
    base = f"{texto}|{imagen}|{musica}"
    return hashlib.sha256(base.encode()).hexdigest()[:12]


def limpiar_y_generar_tags():
    # Backup
    shutil.copy(RUTA, BACKUP)
    print(f"📀 Backup creado en {BACKUP}")

    with open(RUTA, "r", encoding="utf-8") as f:
        data = json.load(f)

    publicados = data.get("publicados", [])

    for v in publicados:

        archivo = v.get("archivo", "")

        # Obtener texto base del archivo
        texto = os.path.basename(archivo).replace(".mp4", "")

        imagen = v.get("imagen", "desconocida")
        musica = v.get("musica", "desconocida")

        # Generar tag aunque la música o imagen sea "desconocida"
        tag = generar_tag(texto, imagen, musica)
        v["tag"] = tag

    # Eliminar arrays que ya no sirven
    if "imagenes" in data:
        del data["imagenes"]

    if "musicas" in data:
        del data["musicas"]

    if "oraciones" in data:
        del data["oraciones"]

    if "salmos" in data:
        del data["salmos"]

    # Guardar historial limpio
    with open(RUTA, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print("✨ Limpieza completada y tag generado para TODOS los videos.")


if __name__ == "__main__":
    limpiar_y_generar_tags()
