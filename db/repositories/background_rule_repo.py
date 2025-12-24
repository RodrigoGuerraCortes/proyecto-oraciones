# db/repositories/background_rule_repo.py

from db.connection import get_connection


def get_background_rules(*, channel_id: int, format_code: str):

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT category, priority, keywords
                FROM background_rules
                WHERE channel_id = %s
                  AND enabled = TRUE
                  AND (format_code IS NULL OR format_code = %s)
                """,
                (channel_id, format_code),
            )
            rules = cur.fetchall()

            cur.execute(
                """
                SELECT fallback
                FROM background_fallback
                WHERE channel_id = %s
                """,
                (channel_id,),
            )
            row = cur.fetchone()

    return rules, (row["fallback"] if row else "default")
