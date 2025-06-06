from pydantic import BaseModel

from app.core.schemas.matches import MatchSchema


class RoundCreate(BaseModel):
    number: int
    draft_id: int


class RoundSchema(RoundCreate):
    id: int
    matches: list[MatchSchema] = []

    class Config:
        from_attributes = True
