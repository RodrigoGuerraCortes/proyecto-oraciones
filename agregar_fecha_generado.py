import json
import shutil
from datetime import datetime

RUTA = "historial.json"
BACKUP = "historial_backup_fecha_generado.json"

def parse_fecha(f):
    try:
        return datetime.fromisoformat(f)
    except:
        return None


def agregar_fecha_generado():
    # Crear backup antes de modificar
    shutil.copy(RUTA, BACKUP)
    print("📀 Backup creado en:", BACKUP)

    # Cargar historial
    with open(RUTA, "r", encoding="utf-8") as f:
        data = json.load(f)

    publicados = data["publicados"]

    corregidos = 0

    for v in publicados:
        # Si ya tiene fecha_generado: NO hacemos nada
        if "fecha_generado" in v and v["fecha_generado"]:
            continue

        fecha_pub = v.get("fecha_publicado")
        if not fecha_pub:
            continue

        # Validar que sea una fecha ISO válida
        if not parse_fecha(fecha_pub):
            continue

        # Asignar fecha_generado = fecha_publicado
        v["fecha_generado"] = fecha_pub
        corregidos += 1

    # Guardar
    with open(RUTA, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"✔ Fecha_generado agregada a {corregidos} videos.")


if __name__ == "__main__":
    agregar_fecha_generado()
