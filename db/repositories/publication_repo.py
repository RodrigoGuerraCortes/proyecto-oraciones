# db/repositories/publication_repo.py

from db.connection import get_connection


def insert_publication(data: dict):
    query = """
        INSERT INTO publications (
            video_id,
            platform_id,
            estado,
            publicar_en,
            fecha_publicado,
            external_id
        )
        VALUES (
            %(video_id)s,
            %(platform_id)s,
            %(estado)s,
            %(publicar_en)s,
            %(fecha_publicado)s,
            %(external_id)s
        );
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, data)
