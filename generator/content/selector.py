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

# Orden editorial fijo de guiones long
GUION_IDS_LONG_ORDEN = [
    "LONG_A",
    "LONG_B",
    "LONG_C",
    "LONG_D",
    "LONG_E",
    "LONG_F",
]


def get_ultimo_guion_usado(channel_id: int) -> str | None:
    """
    Devuelve el último guion_guiado_id usado en videos.tipo='long' para el canal.
    Asume que videos.metadata contiene {"guion_guiado_id": "..."}.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT metadata
                FROM videos
                WHERE channel_id = %s
                  AND tipo = 'long'
                  AND metadata IS NOT NULL
                ORDER BY created_at DESC
                LIMIT 1
            """, (channel_id,))
            row = cur.fetchone()
            if not row:
                return None

            md = row.get("metadata") or {}
            return md.get("guion_guiado_id")

def elegir_siguiente_guion_long(channel_id: int):
    """
    Devuelve (guion_id, guion_guiado) rotando en orden,
    evitando repetir el último guion usado.
    """
    from generator.content.guiones.oracion_guiada_base import GUIÓNES_ORACION_GUIADA_LONG


    ultimo = get_ultimo_guion_usado(channel_id)

    # Primer long del canal
    if not ultimo or ultimo not in GUION_IDS_LONG_ORDEN:
        guion_id = GUION_IDS_LONG_ORDEN[0]
        return guion_id, GUIÓNES_ORACION_GUIADA_LONG[guion_id]

    idx = GUION_IDS_LONG_ORDEN.index(ultimo)
    next_idx = (idx + 1) % len(GUION_IDS_LONG_ORDEN)
    guion_id = GUION_IDS_LONG_ORDEN[next_idx]

    return guion_id, GUIÓNES_ORACION_GUIADA_LONG[guion_id]