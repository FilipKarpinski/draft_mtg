from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.auth.routers import login, users
from app.config import ORIGINS
from app.core.routers import drafts, matches, players

app = FastAPI(title="Draft MTG API", description="API for managing MTG drafts", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(players.router)
app.include_router(matches.router)
app.include_router(drafts.router)
app.include_router(users.router)
app.include_router(login.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to Draft MTG API"}
