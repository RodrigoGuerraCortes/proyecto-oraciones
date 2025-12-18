# generator/content/selector.py
import os
import random
from db.connection import get_connection


def normalizar_slug(nombre: str) -> str:
    """
    Normaliza slugs tipo:
    - c70843d9__salmo_34_algo.mp4 -> salmo_34_algo
    - salmo_34_algo.txt -> salmo_34_algo
    """
    nombre = os.path.basename(nombre)
    nombre = nombre.replace(".mp4", "").replace(".txt", "")
    if "__" in nombre:
        nombre = nombre.split("__", 1)[1]
    return nombre.lower()


def elegir_texto_para(tipo: str, ventana: int = 30):
    carpeta = "textos/salmos" if tipo == "salmo" else "textos/oraciones"

    archivos = [f for f in os.listdir(carpeta) if f.endswith(".txt")]
    if not archivos:
        raise RuntimeError("No hay textos disponibles")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT archivo, texto_base
                FROM videos
                WHERE tipo = %s
                ORDER BY fecha_generado DESC
                LIMIT %s
            """, (tipo, ventana))

            usados_slug = set()
            usados_texto = set()

            for row in cur.fetchall():
                if row["archivo"]:
                    usados_slug.add(normalizar_slug(row["archivo"]))
                if row["texto_base"]:
                    usados_texto.add(row["texto_base"].strip()[:80])

    candidatas = []

    for archivo in archivos:
        slug_txt = normalizar_slug(archivo)
        path = os.path.join(carpeta, archivo)

        with open(path, "r", encoding="utf-8") as f:
            texto = f.read().strip()

        if (
            slug_txt not in usados_slug
            and texto[:80] not in usados_texto
        ):
            candidatas.append(archivo)

    if not candidatas:
        # fallback consciente: prioriza las menos recientes
        candidatas = archivos

    elegido = random.choice(candidatas)
    return os.path.join(carpeta, elegido), elegido.replace(".txt", "")
