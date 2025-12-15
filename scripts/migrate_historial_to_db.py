#!/usr/bin/env python3

import json
import uuid
from datetime import datetime
from pathlib import Path

from db.connection import get_connection
from db.repositories.video_repo import insert_video
from db.repositories.publication_repo import insert_publication
from db.repositories.text_usage_repo import insert_text_usage


# =========================
# Configuración
# =========================
HISTORIAL_PATH = Path("historial.json")
CHANNEL_CODE = "canal_catolico_01"


# =========================
# Helpers
# =========================
def parse_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", ""))
    except Exception:
        return None


def tag_to_uuid(tag: str) -> uuid.UUID:
    """
    Convierte el tag legacy (hex) a UUID determinístico.
    """
    # Normalizamos a 32 chars hex
    tag = tag.strip()
    if len(tag) < 32:
        tag = tag.ljust(32, "0")
    return uuid.UUID(hex=tag[:32])


def get_channel_id_by_code(code: str) -> int:
    query = "SELECT id FROM channels WHERE code = %(code)s"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, {"code": code})
            row = cur.fetchone()
            if not row:
                raise RuntimeError(f"Canal no encontrado: {code}")
            return row["id"]


def get_platform_map() -> dict:
    """
    Retorna: { 'youtube': 1, 'facebook': 2, ... }
    """
    query = "SELECT id, code FROM platforms"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            return {r["code"]: r["id"] for r in rows}


def video_exists(video_id: uuid.UUID) -> bool:
    query = "SELECT 1 FROM videos WHERE id = %(id)s"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, {"id": video_id})
            return cur.fetchone() is not None


# =========================
# Migraciones
# =========================
def migrate_videos(historial: dict, channel_id: int):
    inserted = 0
    skipped = 0

    for item in historial.get("pendientes", []) + historial.get("publicados", []):
        tag = item.get("tag")
        if not tag:
            continue

        video_id = tag_to_uuid(tag)

        if video_exists(video_id):
            skipped += 1
            continue

        archivo = item.get("archivo")
        tipo = item.get("tipo")
        musica = item.get("musica")
        licencia = item.get("licencia")
        imagen = item.get("imagen")
        fecha_generado = parse_datetime(item.get("fecha_generado"))

        # texto_base desde el nombre del archivo
        texto_base = Path(archivo).stem if archivo else "desconocido"

        insert_video({
            "id": video_id,
            "channel_id": channel_id,
            "archivo": archivo,
            "tipo": tipo,
            "musica": musica,
            "licencia": licencia,
            "imagen": imagen,
            "texto_base": texto_base,
            "fecha_generado": fecha_generado or datetime.now(),
        })

        inserted += 1

    return inserted, skipped


def migrate_publications(historial: dict, channel_id: int, platform_map: dict):
    count = 0

    for item in historial.get("pendientes", []) + historial.get("publicados", []):
        tag = item.get("tag")
        plataformas = item.get("plataformas")

        if not tag or not plataformas:
            continue

        video_id = tag_to_uuid(tag)
        publicar_en = parse_datetime(item.get("publicar_en"))

        for platform_code, data in plataformas.items():
            platform_id = platform_map.get(platform_code)
            if not platform_id:
                continue

            estado_json = data.get("estado", "pendiente")
            estado = "published" if estado_json == "publicado" else "scheduled"

            insert_publication({
                "video_id": video_id,
                "platform_id": platform_id,
                "estado": estado,
                "publicar_en": publicar_en or datetime.now(),
                "fecha_publicado": parse_datetime(data.get("fecha_publicado")),
                "external_id": data.get("video_id"),
            })

            count += 1

    return count


def migrate_text_usage(historial: dict, channel_id: int):
    count = 0
    textos = historial.get("textos_usados", {})

    for tipo_path, items in textos.items():
        # tipo_path: textos/oraciones | textos/salmos
        tipo = tipo_path.split("/")[-1].rstrip("s")  # oracion / salmo

        for entry in items:
            insert_text_usage({
                "channel_id": channel_id,
                "video_id": None,
                "tipo": tipo,
                "texto": entry.get("nombre"),
                "used_at": parse_datetime(entry.get("fecha")) or datetime.now(),
            })
            count += 1

    return count


# =========================
# Main
# =========================
def main():
    if not HISTORIAL_PATH.exists():
        raise FileNotFoundError("No se encontró historial.json")

    with HISTORIAL_PATH.open("r", encoding="utf-8") as f:
        historial = json.load(f)

    channel_id = get_channel_id_by_code(CHANNEL_CODE)
    platform_map = get_platform_map()

    print("Iniciando migración...")
    print(f"Canal ID: {channel_id}")
    print(f"Plataformas: {platform_map}")

    v_inserted, v_skipped = migrate_videos(historial, channel_id)
    print(f"Videos insertados: {v_inserted}")
    print(f"Videos duplicados ignorados: {v_skipped}")

    pub_count = migrate_publications(historial, channel_id, platform_map)
    print(f"Publicaciones migradas: {pub_count}")

    text_count = migrate_text_usage(historial, channel_id)
    print(f"Textos usados migrados: {text_count}")

    print("Migración completada con éxito.")


if __name__ == "__main__":
    main()
