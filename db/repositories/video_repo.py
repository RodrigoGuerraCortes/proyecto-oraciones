# db/repositories/video_repo.py

import uuid
from typing import Optional
from db.connection import get_connection
from datetime import datetime, timedelta
from psycopg2.extras import Json

def insert_video(data: dict) -> None:
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
            fingerprint,
            fecha_generado,
            metadata
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
            %(fingerprint)s,
            NOW(),
            %(metadata)s
        );
    """

    # 🔧 ADAPTACIÓN CORRECTA JSON → PostgreSQL
    if "metadata" in data and isinstance(data["metadata"], dict):
        data["metadata"] = Json(data["metadata"])

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, data)




def fingerprint_existe_ultimos_dias(
    fingerprint: str,
    dias: int = 120
) -> bool:
    query = """
        SELECT 1
        FROM videos
        WHERE fingerprint = %(fingerprint)s
          AND fecha_generado >= %(desde)s
        LIMIT 1
    """

    desde = datetime.utcnow() - timedelta(days=dias)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, {
                "fingerprint": fingerprint,
                "desde": desde
            })
            return cur.fetchone() is not None

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
