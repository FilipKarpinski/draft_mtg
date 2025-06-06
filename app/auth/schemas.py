from pydantic import BaseModel, EmailStr, field_validator


class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True
    is_admin: bool = False

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        if not any(char.isdigit() for char in v):
            raise ValueError("password must contain at least one digit")
        if not any(char.isupper() for char in v):
            raise ValueError("password must contain at least one uppercase letter")
        return v


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
