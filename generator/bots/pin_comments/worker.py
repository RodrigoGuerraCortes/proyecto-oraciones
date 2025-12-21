import os
import json
from db.connection import get_connection
from generator.bots.pin_comments.youtube import handle_youtube_first_comment


def is_dry_run() -> bool:
    return os.getenv("DRY_RUN") == "1"


PINNERS = {
    "youtube": handle_youtube_first_comment,
}


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

                    v.id            AS video_internal_id,
                    v.tipo          AS video_tipo,

                    c.id            AS channel_id,
                    c.code          AS channel_code,

                    ca.external_id  AS channel_external_id,
                    ca.username     AS channel_username,
                        
                    v.texto_base    AS video_texto_base

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
        platform = row["platform"]
        handler = PINNERS.get(platform)

        if not handler:
            print(
                f"[PIN WORKER] sin handler para {platform} "
                f"(channel={row['channel_code']})"
            )
            continue

        try:
            result = handler(row, dry_run=dry_run)

            print(
                f"[PIN WORKER][DRY={dry_run}] "
                f"platform={platform} "
                f"channel={row['channel_code']} "
                f"pub={row['publication_id']} "
                f"decision={result['status']}"
            )

            if dry_run:
                print(
                    f"[PIN WORKER][DRY={dry_run}] "
                    f"would create comment: {result.get('comment_text')}"
                )
                continue

            metadata = {
                "comment_text": result.get("comment_text"),
                "ai_model": result.get("ai_model"),
                "prompt_version": result.get("prompt_version"),
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
                        ON CONFLICT ON CONSTRAINT interactions_pinned_unique
                        DO UPDATE SET
                            external_id = EXCLUDED.external_id,
                            status      = EXCLUDED.status,
                            metadata    = EXCLUDED.metadata,
                            updated_at  = NOW()
                    """, (
                        row["publication_id"],
                        row["platform_id"],
                        result.get("external_id"),
                        result["status"],
                        json.dumps(metadata or {}, default=str),
                    ))
                conn.commit()

        except Exception as e:
            print(
                f"[PIN ERROR][DRY={dry_run}] "
                f"{platform} channel={row['channel_code']} "
                f"pub={row['publication_id']} → {e}"
            )

            if dry_run:
                continue

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE interactions
                        SET
                            status = 'failed',
                            error = %s,
                            updated_at = NOW()
                        WHERE publication_id = %s
                          AND platform_id = %s
                          AND type = 'pinned_comment'
                    """, (
                        str(e),
                        row["publication_id"],
                        row["platform_id"],
                    ))
                conn.commit()


if __name__ == "__main__":
    print("[PIN WORKER] entrypoint ejecutado")
    run()
