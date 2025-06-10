from datetime import date
from typing import List

from pydantic import BaseModel

from app.core.schemas.draft_players import DraftPlayerSchema


class DraftBase(BaseModel):
    name: str


class DraftCreate(DraftBase):
    date: date
    player_ids: List[int]


class DraftList(DraftBase):
    id: int
    name: str
    date: date


class DraftFull(BaseModel):
    id: int
    name: str
    date: date
    rounds: List["RoundSchema"] = []
    draft_players: List["DraftPlayerSchema"] = []

    class Config:
        from_attributes = True


from app.core.schemas.rounds import RoundSchema  # noqa: E402

DraftFull.model_rebuild()
