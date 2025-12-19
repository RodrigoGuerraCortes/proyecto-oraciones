# generator/integrations/youtube_api.py

import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaFileUpload

CLIENT_SECRETS_FILE = "client_secret.json"
TOKEN_FILE = "token.pickle"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _get_service():
    creds = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    if not creds:
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
