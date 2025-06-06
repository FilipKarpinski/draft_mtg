from pydantic import BaseModel

from app.core.schemas.matches import MatchSchema


class RoundBase(BaseModel):
    number: int
    draft_id: int


class RoundCreate(RoundBase):
    pass


class RoundSchema(RoundBase):
    id: int
    matches: list[MatchSchema] = []

    class Config:
        from_attributes = True
