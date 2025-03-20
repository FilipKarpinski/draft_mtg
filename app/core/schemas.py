from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class UserBase(BaseModel):
    username: str
    email: str
    is_active: bool = True
    is_admin: bool = False


class UserCreate(UserBase):
    password: str


class UserSchema(UserBase):
    id: int
    hashed_password: str

    class Config:
        from_attributes = True


class PlayerBase(BaseModel):
    name: str
    profile_picture_path: Optional[str] = None


class PlayerCreate(PlayerBase):
    pass


class PlayerSchema(PlayerBase):
    id: int

    class Config:
        from_attributes = True


class DraftBase(BaseModel):
    player_id: int
    draft_date: datetime


class DraftCreate(DraftBase):
    pass


class DraftSchema(DraftBase):
    id: int
    matches: List["MatchSchema"] = []

    class Config:
        from_attributes = True


class MatchBase(BaseModel):
    player_1_id: int
    player_2_id: int
    score_1: int
    score_2: int
    draft_id: int


class MatchCreate(MatchBase):
    pass


class MatchSchema(MatchBase):
    id: int
    draft: DraftSchema
    player_1: PlayerSchema
    player_2: PlayerSchema

    class Config:
        from_attributes = True


# Needed to resolve forward references
MatchSchema.model_rebuild()
DraftSchema.model_rebuild()
