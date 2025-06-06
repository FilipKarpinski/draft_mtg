from pydantic import BaseModel

from app.core.models import Color


class DraftPlayerSchema(BaseModel):
    draft_id: int
    player_id: int
    deck_colors: list[Color] = []
    points: int = 0
    final_place: int | None = None
    order: int

    class Config:
        from_attributes = True
