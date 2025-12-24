# generator/v2/content/selector.py

import os
import random
from typing import Tuple
from db.connection import get_connection


def normalizar_slug(nombre: str) -> str:
    nombre = os.path.basename(nombre)
    nombre = nombre.replace(".mp4", "").replace(".txt", "")
    if "__" in nombre:
        nombre = nombre.split("__", 1)[1]
    return nombre.lower()


def _obtener_usados_db(
    *,
    channel_id: int,
    internal_type: str,
    ventana: int,
    db_conn=None
) -> tuple[set, set]:
    """
    Obtiene slugs y textos recientemente usados desde BD.
    """
    conn = db_conn or get_connection()

    usados_slug = set()
    usados_texto = set()

    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT archivo, texto_base
                FROM videos
                WHERE channel_id = %s
                  AND tipo = %s
                ORDER BY fecha_generado DESC
                LIMIT %s
            """, (channel_id, internal_type, ventana))

            for row in cur.fetchall():
                if row.get("archivo"):
                    usados_slug.add(normalizar_slug(row["archivo"]))
                if row.get("texto_base"):
                    usados_texto.add(row["texto_base"].strip()[:80])

    return usados_slug, usados_texto


def elegir_texto_para(
    *,
    channel_id: int,
    format_key: str,
    channel_config: dict,
    ventana: int = 30,
    db_conn=None
) -> Tuple[str, str]:
    """
    Retorna (path_txt, base_name)
    """

    formats = channel_config["formats"]

    if format_key not in formats:
        raise ValueError(f"Formato no definido: {format_key}")

    fmt = formats[format_key]
    content_cfg = fmt["content"]

    internal_type = content_cfg["type"]
    base_path = channel_config["content"]["base_path"]
    carpeta = os.path.join(base_path, content_cfg["path"])

    if not os.path.isdir(carpeta):
        raise RuntimeError(f"Carpeta de textos no existe: {carpeta}")

    archivos = [f for f in os.listdir(carpeta) if f.endswith(".txt")]
    if not archivos:
        raise RuntimeError("No hay textos disponibles")

    usados_slug, usados_texto = _obtener_usados_db(
        channel_id=channel_id,
        internal_type=internal_type,
        ventana=ventana,
        db_conn=db_conn
    )

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
        # fallback consciente
        candidatas = archivos

    elegido = random.choice(candidatas)
    return os.path.join(carpeta, elegido), elegido.replace(".txt", "")
