import os
import json
from db.connection import get_connection

from generator.bots.reply_comments.youtube import (
    list_top_level_comments,
    is_comment_from_channel,
    has_reply_from_channel,
)

from generator.bots.reply_comments.ai.youtube_generator import generate_reply
from generator.integrations.youtube_api import create_reply_comment

# -------------------------------------------------
# Configuración
# -------------------------------------------------
MAX_REPLIES_PER_VIDEO = 2


def is_dry_run() -> bool:
    return os.getenv("DRY_RUN") == "1"


# -------------------------------------------------
# DB helpers
# -------------------------------------------------
def reply_already_sent(parent_comment_id: str) -> bool:
    """
    Verifica si ya existe una respuesta registrada
    para este comentario (idempotencia).
    """
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


def save_interaction(
    *,
    publication_id: int,
    platform_id: int,
    parent_comment_id: str,
    reply_text: str,
    ai_meta: dict,
    author: str,
    external_id: str,
):
    """
    Guarda la interacción de reply en BD.
    """
    metadata = {
        "parent_comment_id": parent_comment_id,
        "reply_text": reply_text,
        "model": ai_meta["model"],
        "prompt_version": ai_meta["prompt_version"],
        "author": author,
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
                publication_id,
                platform_id,
                external_id,  # external_id (reply_id cuando pasemos a ejecución real)
                json.dumps(metadata),
            ))
        conn.commit()


# -------------------------------------------------
# Worker principal
# -------------------------------------------------
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

                JOIN system_config sc
                  ON sc.key = 'bootstrap_date'

                WHERE p.estado = 'published'
                  AND p.publicar_en >= sc.value
                  AND pl.code = 'youtube'

                ORDER BY p.created_at ASC;
            """)
            rows = cur.fetchall()

    print(f"[REPLY WORKER] publicaciones encontradas: {len(rows)}")

    # -------------------------------------------------
    # Procesar publicaciones
    # -------------------------------------------------
    for row in rows:
        video_id = row["video_id"]
        channel_id = row["channel_external_id"]
        replies_sent = 0

        print(
            f"\n[REPLY WORKER] Revisando video={video_id} "
            f"(channel={row['channel_code']})"
        )

        comments = list_top_level_comments(video_id)

        # Comentarios deshabilitados
        if isinstance(comments, dict) and comments.get("error") == "comments_disabled":
            print(f"[SKIP] comments_disabled video={video_id}")
            continue

        for c in comments:
            if replies_sent >= MAX_REPLIES_PER_VIDEO:
                print("[INFO] max_replies_per_video alcanzado")
                break

            comment_id = c["id"]
            snippet = c["snippet"]["topLevelComment"]["snippet"]
            text = snippet["textDisplay"]
            author = snippet.get("authorDisplayName")

            # 1) Comentario del propio canal
            if is_comment_from_channel(c, channel_id):
                print(f"[SKIP] own_comment id={comment_id}")
                continue

            # 2) Ya tiene reply del canal en YouTube
            if has_reply_from_channel(c, channel_id):
                print(f"[SKIP] already_replied id={comment_id}")
                continue

            # 3) Ya respondido por este bot
            if reply_already_sent(comment_id):
                print(f"[SKIP] reply_already_sent id={comment_id}")
                continue

            # 4) Generar reply con IA
            context = {
                "channel_name": row["channel_username"],
                "user_comment": text,
            }

            ai_result = generate_reply(context)

            print(
                f"[WOULD_REPLY] id={comment_id} "
                f"author={author} "
                f"text='{text[:40]}...' "
                f"reply='{ai_result['text']}'"
            )

            # 5) DRY-RUN → no persistir
            if dry_run:
                replies_sent += 1
                continue

            reply_id = create_reply_comment(
                parent_comment_id=comment_id,
                text=ai_result["text"],
            )

            # 6) Guardar interacción
            save_interaction(
                publication_id=row["publication_id"],
                platform_id=row["platform_id"],
                parent_comment_id=comment_id,
                reply_text=ai_result["text"],
                ai_meta=ai_result,
                author=author,
                external_id=reply_id,
            )

            replies_sent += 1


# -------------------------------------------------
# Entrypoint
# -------------------------------------------------
if __name__ == "__main__":
    print("[REPLY WORKER] entrypoint ejecutado")
    run()
