import os

from dotenv import load_dotenv
from passlib.context import CryptContext

load_dotenv()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
SECRET_KEY = os.getenv("SECRET_KEY")

PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")

ORIGINS = [
    "http://localhost",
    "http://localhost:8080",
]
