# generator/v3/publications/run_scheduler.py

from db.connection import get_connection
from generator.v3.publications.crear_publications import crear_publications


def get_canales_activos():
    # ajusta nombres de tabla/campo según tu DB real
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id
                FROM channels
                WHERE activo = true
            """)
            return [row["id"] for row in cur.fetchall()]


def main(dias: int = 7):
    canales = get_canales_activos()
    for channel_id in canales:
        creadas = crear_publications(channel_id=channel_id, dias=dias)
        print(f"[SCHEDULER] channel={channel_id} publicaciones_creadas={len(creadas)}")


if __name__ == "__main__":
    main(dias=7)
