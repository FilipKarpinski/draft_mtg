from pydantic import BaseModel

from app.core.schemas.players import PlayerSchema


class MatchBase(BaseModel):
    player_1_id: int
    player_2_id: int
    score: str | None = None
    round_id: int


class MatchCreate(MatchBase):
    pass


class MatchSchema(MatchBase):
    id: int
    player_1: PlayerSchema
    player_2: PlayerSchema

    class Config:
        from_attributes = True


MatchSchema.model_rebuild()
