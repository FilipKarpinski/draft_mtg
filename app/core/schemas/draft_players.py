from pydantic import BaseModel, model_validator


class DraftPlayerSchema(BaseModel):
    draft_id: int
    player_id: int
    final_place: int | None = None
    order: int | None = None

    class Config:
        from_attributes = True


class DraftPlayerSetOrdersSchema(BaseModel):
    player_orders: dict[int, int]

    @model_validator(mode="after")
    def validate_player_orders(self) -> "DraftPlayerSetOrdersSchema":
        if len(set(self.player_orders.values())) != len(self.player_orders):
            raise ValueError("All player_orders must have unique values")
        return self
