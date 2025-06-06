from datetime import date
from typing import List

from pydantic import BaseModel

from app.core.schemas.draft_players import DraftPlayerSchema


class DraftBase(BaseModel):
    name: str


class DraftCreate(DraftBase):
    date: date
    player_ids: List[int]


class DraftSchemaBase(DraftBase):
    id: int

    class Config:
        from_attributes = True


class DraftSchema(DraftSchemaBase):
    rounds: List["RoundSchema"] = []
    draft_players: List["DraftPlayerSchema"] = []

    class Config:
        from_attributes = True


from app.core.schemas.rounds import RoundSchema  # noqa: E402

DraftSchema.model_rebuild()
