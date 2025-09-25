from passlib.context import CryptContext
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DEBUG: bool = False
    # JWT settings
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 30 * 60  # 30 minutes
    REFRESH_TOKEN_EXPIRE_SECONDS: int = 30 * 24 * 60 * 60  # 30 days
    SECRET_KEY: str = "somerandomkey"
    REFRESH_TOKEN_SECRET_KEY: str = "anotherverysecretkey"  # Different key for refresh tokens

    # Database settings
    POSTGRES_HOST: str = "db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "postgres"

    # CORS settings
    ORIGINS: list[str] = [
        "http://localhost",
        "http://localhost:8080",
        "https://draft-mtg.jako-tako-software.work",
        "http://draft-mtg.jako-tako-software.work",
        "http://localhost:5173",
        "https://draft.jako-tako-software.work",
    ]

    # Password hashing
    PWD_CONTEXT: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Create settings instance
settings = Settings()
