from pydantic import BaseModel


class UserBase(BaseModel):
    username: str
    email: str
    is_active: bool
    is_admin: bool


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserSchema(UserBase):
    id: int
    hashed_password: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
