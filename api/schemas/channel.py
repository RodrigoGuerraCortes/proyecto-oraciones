from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ChannelOut(BaseModel):
    id: int
    code: str
    name: str
    active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

