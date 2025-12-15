# db/repositories/text_usage_repo.py

from db.connection import get_connection


def insert_text_usage(data: dict):
    query = """
        INSERT INTO text_usage (
            channel_id,
            video_id,
            tipo,
            texto,
            used_at
        )
        VALUES (
            %(channel_id)s,
            %(video_id)s,
            %(tipo)s,
            %(texto)s,
            %(used_at)s
        );
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, data)
