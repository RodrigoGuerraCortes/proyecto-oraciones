# generator/bots/pin_comments/handlers/youtube.py

from integrations.youtube_api import (
    get_video_status,
    has_top_level_comment_from_channel,
    create_first_comment,
)

from bots.pin_comment.ai.generator import generate_pin_comment


def handle_youtube_pin_comment(row: dict, *, dry_run: bool) -> dict:
    """
    Ejecuta el pin comment para YouTube.
    NO toca DB.
    """
    video_id = row["video_id"]
    channel_external_id = row["channel_external_id"]

    # 1. Ver estado del video
    status = get_video_status(video_id)
    if status["privacyStatus"] != "public":
        return {
            "status": "skipped_not_public",
            "external_id": None,
        }

    # 2. ¿Ya existe comentario del canal?
    if has_top_level_comment_from_channel(video_id, channel_external_id):
        return {
            "status": "skipped_existing",
            "external_id": None,
        }

    # 3. Generar texto IA
    context = {
        "channel_name": row["channel_username"],
        "video_tipo": row["video_tipo"],
        "video_texto_base": row.get("video_texto_base"),
    }

    ai_result = generate_pin_comment(context)

    if dry_run:
        return {
            "status": "would_create",
            "external_id": None,
            "comment_text": ai_result["text"],
            "ai_meta": ai_result,
        }

    # 4. Crear comentario real
    comment_id = create_first_comment(
        video_id=video_id,
        text=ai_result["text"],
    )

    return {
        "status": "done",
        "external_id": comment_id,
        "comment_text": ai_result["text"],
        "ai_meta": ai_result,
    }
