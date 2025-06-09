from pydantic import BaseModel

from app.core.models import Color
from app.core.schemas.players import PlayerSchema


class DraftPlayerSchema(BaseModel):
    draft_id: int
    player: PlayerSchema
    deck_colors: list[Color] = []
    points: int = 0
    final_place: int | None = None
    order: int

    class Config:
        from_attributes = True


class DraftPlayerUpdate(BaseModel):
    deck_colors: list[str] | None = None
    points: int | None = None
    final_place: int | None = None

    class Config:
        from_attributes = True
