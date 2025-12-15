# db/repositories/video_repo.py

import uuid
from typing import Optional
from db.connection import get_connection


def insert_video(data: dict) -> uuid.UUID:
    query = """
        INSERT INTO videos (
            id,
            channel_id,
            archivo,
            tipo,
            musica,
            licencia,
            imagen,
            texto_base,
            fecha_generado
        )
        VALUES (
            %(id)s,
            %(channel_id)s,
            %(archivo)s,
            %(tipo)s,
            %(musica)s,
            %(licencia)s,
            %(imagen)s,
            %(texto_base)s,
            %(fecha_generado)s
        );
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, data)

    return data["id"]


def get_video_by_id(video_id: uuid.UUID) -> Optional[dict]:
    query = """
        SELECT *
        FROM videos
        WHERE id = %(id)s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, {"id": video_id})
            return cur.fetchone()
