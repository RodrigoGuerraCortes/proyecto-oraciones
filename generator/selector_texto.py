# generator/selector_texto.py
import os
import random
from typing import Optional
from db.connection import get_connection


def normalizar_slug(nombre: str) -> str:
    nombre = os.path.basename(nombre)
    nombre = nombre.replace(".mp4", "").replace(".txt", "")
    if "__" in nombre:
        nombre = nombre.split("__", 1)[1]
    return nombre.lower()


def elegir_texto(
    *,
    content_base_path: str,
    tipo: str,
    ventana: int = 30,
    archivo_forzado: str | None = None,
):
    """
    Devuelve:
      - text_path (absoluto)
      - slug_base (para DB / filename lógico)
      - texto_base (contenido)
    """

    # -----------------------------------------
    # FORZADO (debug / test)
    # -----------------------------------------
    if archivo_forzado:
        full_path = os.path.join(content_base_path, archivo_forzado)
        with open(full_path, "r", encoding="utf-8") as f:
            texto = f.read().strip()

        return full_path, normalizar_slug(archivo_forzado), texto

    print("[DECIDE - TXT] No se forzó archivo, eligiendo aleatoriamente")

    carpeta = content_base_path
    
    
    archivos = [f for f in os.listdir(carpeta) if f.endswith(".txt")]



    if not archivos:
        raise RuntimeError(f"No hay textos en {carpeta}")

    usados_slug = set()
    usados_texto = set()

    print(f"[DECIDE - TXT] buscando en carpeta={carpeta}")
    print(f"[DECIDE - TXT] archivos_disponibles={len(archivos)}")
    print(f"[DECIDE - TXT] ventana_dias={ventana}")
    print(f"[DECIDE - TXT] tipo={tipo}")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT archivo, texto_base
                FROM videos
                WHERE tipo = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (tipo, ventana),
            )

            for row in cur.fetchall():
                if row["archivo"]:
                    usados_slug.add(normalizar_slug(row["archivo"]))
                if row["texto_base"]:
                    usados_texto.add(row["texto_base"][:80])

    candidatas = []

    for archivo in archivos:
        slug = normalizar_slug(archivo)
        path = os.path.join(carpeta, archivo)

        with open(path, "r", encoding="utf-8") as f:
            texto = f.read().strip()

        if slug not in usados_slug and texto[:80] not in usados_texto:
            candidatas.append((archivo, texto))

    if not candidatas:
        candidatas = [(a, open(os.path.join(carpeta, a), encoding="utf-8").read().strip()) for a in archivos]

    elegido, texto = random.choice(candidatas)

    print(f"[DECIDE - TXT] tipo={tipo} usados={len(usados_slug)} candidatas={len(candidatas)} elegido={elegido}")
    print(f"[DECIDE - TXT] texto_preview={texto[:60]!r}")
    print(f"[DECIDE - TXT] {os.path.join(carpeta, elegido)}")
    print(f"[DECIDE - TXT] slug={normalizar_slug(elegido)}")
    return (
        os.path.join(carpeta, elegido),
        normalizar_slug(elegido),
        texto,
    )


# -------------------------------------------------
# Selector de guiones long (editorial)
# -------------------------------------------------
GUION_IDS_LONG_ORDEN = [
    "LONG_A",
    "LONG_B",
    "LONG_C",
    "LONG_D",
    "LONG_E",
    "LONG_F",
]


def get_ultimo_guion_usado(channel_id: int) -> Optional[str]:
    """
    Devuelve el último guion_guiado_id usado por el canal.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT metadata
                FROM videos
                WHERE channel_id = %s
                  AND tipo LIKE 'long%%'
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
    Devuelve (guion_id, guion_contenido) rotando en orden editorial.
    """
    from generator.content.guiones.oracion_guiada_base import (
        GUIÓNES_ORACION_GUIADA_LONG,
    )

    ultimo = get_ultimo_guion_usado(channel_id)

    if not ultimo or ultimo not in GUION_IDS_LONG_ORDEN:
        guion_id = GUION_IDS_LONG_ORDEN[0]
        return guion_id, GUIÓNES_ORACION_GUIADA_LONG[guion_id]

    idx = GUION_IDS_LONG_ORDEN.index(ultimo)
    next_idx = (idx + 1) % len(GUION_IDS_LONG_ORDEN)
    guion_id = GUION_IDS_LONG_ORDEN[next_idx]

    return guion_id, GUIÓNES_ORACION_GUIADA_LONG[guion_id]
