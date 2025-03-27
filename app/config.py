import os

from dotenv import load_dotenv
from passlib.context import CryptContext

load_dotenv()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
SECRET_KEY = os.getenv("SECRET_KEY")

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@db:{POSTGRES_PORT}/{POSTGRES_DB}"


PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")

ORIGINS = [
    "http://localhost",
    "http://localhost:8080",
    "https://draft-mtg.jako-tako-software.work",
    "http://draft-mtg.jako-tako-software.work",
]
