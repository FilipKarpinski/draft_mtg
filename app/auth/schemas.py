from pydantic import BaseModel


class UserBase(BaseModel):
    email: str
    is_active: bool
    is_admin: bool


class UserCreate(BaseModel):
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
    email: str | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
