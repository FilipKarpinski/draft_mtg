from pydantic import BaseModel


class PlayerBase(BaseModel):
    name: str


class PlayerCreate(PlayerBase):
    pass


class PlayerSchema(PlayerBase):
    id: int

    class Config:
        from_attributes = True
