from typing import Optional

from pydantic import BaseModel


class PlayerBase(BaseModel):
    name: str
    profile_picture_path: Optional[str] = None


class PlayerCreate(PlayerBase):
    pass


class PlayerSchema(PlayerBase):
    id: int

    class Config:
        from_attributes = True
