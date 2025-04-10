from pydantic import BaseModel

from app.core.schemas.drafts import DraftSchemaBase
from app.core.schemas.players import PlayerSchema


class MatchBase(BaseModel):
    round: int
    player_1_id: int
    player_2_id: int
    score: str | None = None
    draft_id: int


class MatchCreate(MatchBase):
    pass


class MatchSchema(MatchBase):
    id: int
    draft: "DraftSchemaBase"
    player_1: PlayerSchema
    player_2: PlayerSchema

    class Config:
        from_attributes = True


MatchSchema.model_rebuild()
