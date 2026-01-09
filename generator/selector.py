# generator/selector.py

import os
import random
from db.connection import get_connection

EXT_VALIDAS = (".jpg", ".jpeg", ".png", ".webp")


def elegir_imagen_por_categoria(
    categoria: str,
    ventana: int = 10,
    base_path_assest: str = None,
) -> tuple[str, str]:
    """
    Retorna:
    - ruta_relativa: ej 'jesus/30.png'
    - categoria
    """

    base_dir = os.path.join(base_path_assest, categoria)

    if not os.path.isdir(base_dir):
        raise RuntimeError(f"Categoría no existe: {categoria}")

    archivos = [
        f for f in os.listdir(base_dir)
        if f.lower().endswith(EXT_VALIDAS)
    ]

    if not archivos:
        raise RuntimeError(f"No hay imágenes en {categoria}")

    # 1️⃣ imágenes usadas recientemente desde BD
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT imagen
                FROM videos
                WHERE imagen LIKE %s
                ORDER BY fecha_generado DESC
                LIMIT %s
            """, (f"{categoria}/%", ventana))

            usadas = {
                row["imagen"].split("/")[-1]
                for row in cur.fetchall()
                if row.get("imagen")
            }

    # 2️⃣ filtrar
    candidatas = [f for f in archivos if f not in usadas]
    if not candidatas:
        candidatas = archivos  # fallback consciente

    print(f"[DECIDE - IMG] categoria={categoria} usadas={len(usadas)} candidatas={len(candidatas)}")


    elegida = random.choice(candidatas)
    return f"{categoria}/{elegida}", categoria
