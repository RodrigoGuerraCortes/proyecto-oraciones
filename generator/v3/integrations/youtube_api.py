# generator/v3/integrations/youtube_api.py

import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

CLIENT_SECRETS_FILE = "client_secret.json"
TOKEN_FILE = "token.pickle"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.force-ssl",]

def _get_service():
    creds = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    # -------------------------------
    # REFRESH TOKEN SI ES NECESARIO
    # -------------------------------
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(TOKEN_FILE, "wb") as token:
                pickle.dump(creds, token)
        except RefreshError:
            raise RuntimeError(
                "OAuth token inválido o revocado. Reautoriza YouTube API."
            )

    # -------------------------------
    # NO HAY CREDENCIALES → AUTH FLOW
    # -------------------------------
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, SCOPES
        )
        creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    return build("youtube", "v3", credentials=creds)

def upload_video(
    *,
    ruta,
    titulo,
    descripcion,
    tags,
    privacidad,
    publish_at,
):
    youtube = _get_service()

    status_body = (
        {"privacyStatus": "private", "publishAt": publish_at}
        if publish_at
        else {"privacyStatus": privacidad}
    )

    request_body = {
        "snippet": {
            "title": titulo,
            "description": descripcion,
            "tags": tags,
            "categoryId": "22",
        },
        "status": status_body,
    }

    media = MediaFileUpload(
        ruta, chunksize=1024 * 1024, resumable=True
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media,
    )

    response = None
    while response is None:
        _, response = request.next_chunk()

    return response.get("id")


def list_video_comments(video_id: str) -> list:
    youtube = _get_service()
    comments = []

    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=100,
        textFormat="plainText"
    )

    while request:
        response = request.execute()
        comments.extend(response.get("items", []))
        request = youtube.commentThreads().list_next(request, response)

    return comments

def has_top_level_comment_from_channel(video_id: str, channel_id: str) -> bool:
    comments = list_video_comments(video_id)

    for c in comments:
        author = c["snippet"]["topLevelComment"]["snippet"].get("authorChannelId")
        if author and author["value"] == channel_id:
            return True

    return False

def create_first_comment(video_id: str, text: str) -> str:
    youtube = _get_service()

    response = youtube.commentThreads().insert(
        part="snippet",
        body={
            "snippet": {
                "videoId": video_id,
                "topLevelComment": {
                    "snippet": {
                        "textOriginal": text
                    }
                }
            }
        }
    ).execute()

    return response["snippet"]["topLevelComment"]["id"]


def get_video_status(video_id: str) -> dict:
    youtube = _get_service()

    resp = youtube.videos().list(
        part="status",
        id=video_id
    ).execute()

    if not resp["items"]:
        raise RuntimeError("Video no encontrado")

    return resp["items"][0]["status"]


def create_reply_comment(parent_comment_id: str, text: str) -> str:
    youtube = _get_service()

    response = youtube.comments().insert(
        part="snippet",
        body={
            "snippet": {
                "parentId": parent_comment_id,
                "textOriginal": text,
            }
        }
    ).execute()

    return response["id"]
