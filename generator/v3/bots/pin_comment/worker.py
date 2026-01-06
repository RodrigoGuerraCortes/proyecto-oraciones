# generator/bots/pin_comments/worker.py

import os
import json
from db.connection import get_connection

from generator.v3.bots.pin_comment.handler.youtube import (
    handle_youtube_pin_comment,
)

PIN_HANDLERS = {
    "youtube": handle_youtube_pin_comment,
}


def is_dry_run() -> bool:
    return os.getenv("DRY_RUN") == "1"


def run():
    dry_run = is_dry_run()
    print(f"[PIN WORKER] DRY_RUN={'ON' if dry_run else 'OFF'}")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    p.id            AS publication_id,
                    p.external_id   AS video_id,
                    p.created_at,

                    pl.id           AS platform_id,
                    pl.code         AS platform,

                    v.tipo          AS video_tipo,
                    v.texto_base    AS video_texto_base,

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

                JOIN system_config sc
                  ON sc.key = 'bootstrap_date'

                LEFT JOIN interactions i
                  ON i.publication_id = p.id
                 AND i.platform_id = pl.id
                 AND i.type = 'pinned_comment'
                 AND i.status IN ('done', 'skipped_existing')

                WHERE p.estado = 'published'
                  AND p.created_at >= sc.value
                  AND i.id IS NULL

                ORDER BY p.created_at ASC;
            """)
            rows = cur.fetchall()

    print(f"[PIN WORKER] publicaciones encontradas: {len(rows)}")

    for row in rows:
        handler = PIN_HANDLERS.get(row["platform"])
        if not handler:
            continue

        try:
            result = handler(row, dry_run=dry_run)

            print(
                f"[PIN] pub={row['publication_id']} "
                f"platform={row['platform']} "
                f"status={result['status']}"
            )

            if dry_run:
                print(f"[PIN][DRY] {result.get('comment_text')}")
                continue

            metadata = {
                "comment_text": result.get("comment_text"),
                **(result.get("ai_meta") or {}),
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
                        VALUES (%s, %s, 'pinned_comment', %s, %s, %s)
                    """, (
                        row["publication_id"],
                        row["platform_id"],
                        result.get("external_id"),
                        result["status"],
                        json.dumps(metadata),
                    ))
                conn.commit()

        except Exception as e:
            print(
                f"[PIN ERROR] pub={row['publication_id']} "
                f"platform={row['platform']} → {e}"
            )


if __name__ == "__main__":
    print("[PIN WORKER] entrypoint ejecutado")
    run()
