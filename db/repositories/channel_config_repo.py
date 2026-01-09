from db.connection import get_connection


def get_channel_config(channel_id: int) -> dict:
    """
    Retorna el JSON config del canal.
    Lanza error si no existe.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT config
                FROM channel_configs
                WHERE channel_id = %s
                  AND active = true
                """,
                (channel_id,)
            )
            row = cur.fetchone()

            if not row:
                raise RuntimeError(
                    f"No existe configuración activa para channel_id={channel_id}"
                )

            return row["config"]
