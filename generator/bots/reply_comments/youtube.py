from generator.integrations.youtube_api import _get_service
from googleapiclient.errors import HttpError

def list_top_level_comments(video_id: str) -> list:
    youtube = _get_service()
    comments = []

    try:
        request = youtube.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            maxResults=100,
            textFormat="plainText",
        )

        while request:
            response = request.execute()
            comments.extend(response.get("items", []))
            request = youtube.commentThreads().list_next(request, response)

    except HttpError as e:
        if e.resp.status == 403:
            return {"error": "comments_disabled"}
        raise

    return comments


def is_comment_from_channel(comment: dict, channel_id: str) -> bool:
    author = comment["snippet"]["topLevelComment"]["snippet"].get("authorChannelId")
    return author and author["value"] == channel_id


def has_reply_from_channel(comment: dict, channel_id: str) -> bool:
    replies = comment.get("replies", {}).get("comments", [])
    for r in replies:
        author = r["snippet"].get("authorChannelId")
        if author and author["value"] == channel_id:
            return True
    return False
