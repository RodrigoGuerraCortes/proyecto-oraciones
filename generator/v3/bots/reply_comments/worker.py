# generator/v3/bots/reply_comment/worker.py

import os
import json
from db.connection import get_connection
from generator.v3.bots.reply_comments.handler.youtube import handle_youtube_replies


def is_dry_run() -> bool:
    return os.getenv("DRY_RUN") == "1"


def reply_already_sent(parent_comment_id: str) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 1
                FROM interactions
                WHERE type = 'comment_reply'
                  AND metadata->>'parent_comment_id' = %s
                LIMIT 1
            """, (parent_comment_id,))
            return cur.fetchone() is not None


def run():
    dry_run = is_dry_run()
    print(f"[REPLY WORKER] DRY_RUN={'ON' if dry_run else 'OFF'}")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    p.id            AS publication_id,
                    p.external_id   AS video_id,

                    pl.id           AS platform_id,
                    pl.code         AS platform,

                    c.code          AS channel_code,
                    ca.external_id  AS channel_external_id,
                    ca.username     AS channel_username

                FROM publications p
                JOIN platforms pl ON pl.id = p.platform_id
                JOIN videos v     ON v.id = p.video_id
                JOIN channels c   ON c.id = v.channel_id
                JOIN channel_accounts ca
                  ON ca.channel_id = c.id
                 AND ca.platform_id = pl.id
                 AND ca.active = true

                WHERE p.estado = 'published'
                  AND pl.code = 'youtube'

                ORDER BY p.created_at ASC;
            """)
            rows = cur.fetchall()

    print(f"[REPLY WORKER] publicaciones encontradas: {len(rows)}")

    for row in rows:
        actions = handle_youtube_replies(
            row,
            dry_run=dry_run,
            reply_already_sent=reply_already_sent,
        )

        for act in actions:
            print(
                f"[REPLY] pub={row['publication_id']} "
                f"status={act['status']} "
                f"author={act.get('author')}"
            )

            if act["status"] == "would_reply":
                print("─" * 40)
                print(act["reply_text"])
                print("─" * 40)


            if act["status"] != "done":
                continue

            metadata = {
                "parent_comment_id": act["parent_comment_id"],
                "reply_text": act["reply_text"],
                **act["ai_meta"],
                "author": act["author"],
            }

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO interactions
                        (
                            publication_id,
                            platform_id,
                            type,
                            external_id,
                            status,
                            metadata
                        )
                        VALUES (%s, %s, 'comment_reply', %s, 'done', %s)
                    """, (
                        row["publication_id"],
                        row["platform_id"],
                        act["external_id"],
                        json.dumps(metadata),
                    ))
                conn.commit()


if __name__ == "__main__":
    print("[REPLY WORKER] entrypoint ejecutado")
    run()
