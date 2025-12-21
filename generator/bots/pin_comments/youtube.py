from googleapiclient.errors import HttpError
from generator.integrations.youtube_api import (
    has_top_level_comment_from_channel,
    create_first_comment,
    get_video_status,
)
from generator.bots.pin_comments.ai.youtube_generator import (
    generate_ai_comment,
)

YOUTUBE_FIRST_COMMENT_TEXT = (
    "🙏 ¿Te unes a esta oración?\n"
    "Déjanos tu intención en los comentarios y acompáñanos cada día. 🤍"
)

def handle_youtube_first_comment(row: dict, dry_run: bool) -> dict:
    video_id = row["video_id"]
    channel_external_id = row["channel_external_id"]

    # 1. Estado del video
    status = get_video_status(video_id)
    privacy = status["privacyStatus"]

    # ⏳ Video aún no público
    if privacy != "public":
        return {
            "status": "skipped_not_public",
            "external_id": None,
        }

    # 2. ¿Ya existe comentario?
    exists = has_top_level_comment_from_channel(
        video_id=video_id,
        channel_id=channel_external_id,
    )

    if exists:
        return {
            "status": "skipped_existing",
            "external_id": None,
        }
    

    # 3. Generar texto IA (SIEMPRE, incluso en dry-run)
    context = {
        "channel_name": row["channel_username"],
        "video_tipo": row["video_tipo"],
        "video_texto_base": row["video_texto_base"],
    }

    ai_result = generate_ai_comment(context)

    
    # 4. DRY-RUN: NO crear comentario
    if dry_run:
        return {
            "status": "would_create_comment",
            "external_id": None,
            "comment_text": ai_result["text"],
        }

    # 5. EJECUCIÓN REAL
    comment_id = create_first_comment(
        video_id=video_id,
        text=ai_result["text"],
    )

    return {
        "status": "done",
        "external_id": comment_id,
    }
