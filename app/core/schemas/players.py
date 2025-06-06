from pydantic import BaseModel


class PlayerCreate(BaseModel):
    name: str


class PlayerSchema(PlayerCreate):
    id: int

    class Config:
        from_attributes = True
