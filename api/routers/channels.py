from fastapi import APIRouter
from api.schemas.channel import ChannelOut
from db.repositories.channel_repo import list_channels

router = APIRouter(prefix="/channels", tags=["channels"])


@router.get("", response_model=list[ChannelOut])
def get_channels():
    return list_channels()
