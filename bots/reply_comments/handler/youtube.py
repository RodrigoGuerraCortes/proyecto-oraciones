# bots/reply_comment/handler/youtube.py

from bots.reply_comments.ai.generator import generate_reply
from integrations.youtube_api import create_reply_comment
from bots.reply_comments.handler.youtube_handler import (
    list_top_level_comments,
    is_comment_from_channel,
    has_reply_from_channel,
)


MAX_REPLIES_PER_VIDEO = 2


def handle_youtube_replies(row: dict, *, dry_run: bool, reply_already_sent) -> list:
    """
    Retorna una lista de acciones realizadas (o que se realizarían).
    """
    video_id = row["video_id"]
    channel_id = row["channel_external_id"]
    channel_name = row["channel_username"]

    actions = []
    replies_sent = 0

    comments = list_top_level_comments(video_id)

    if isinstance(comments, dict) and comments.get("error") == "comments_disabled":
        return actions

    for c in comments:
        if replies_sent >= MAX_REPLIES_PER_VIDEO:
            break

        comment_id = c["id"]
        snippet = c["snippet"]["topLevelComment"]["snippet"]
        text = snippet["textDisplay"]
        author = snippet.get("authorDisplayName")

        if is_comment_from_channel(c, channel_id):
            continue

        if has_reply_from_channel(c, channel_id):
            continue

        if reply_already_sent(comment_id):
            continue

        context = {
            "channel_name": channel_name,
            "user_comment": text,
        }

        ai_result = generate_reply(context)

        if dry_run:
            actions.append({
                "status": "would_reply",
                "parent_comment_id": comment_id,
                "reply_text": ai_result["text"],
                "ai_meta": ai_result,
                "author": author,
            })
            replies_sent += 1
            continue

        reply_id = create_reply_comment(
            parent_comment_id=comment_id,
            text=ai_result["text"],
        )

        actions.append({
            "status": "done",
            "parent_comment_id": comment_id,
            "external_id": reply_id,
            "reply_text": ai_result["text"],
            "ai_meta": ai_result,
            "author": author,
        })

        replies_sent += 1

    return actions


