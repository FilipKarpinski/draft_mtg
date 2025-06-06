from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routers import login, users
from app.config import settings
from app.core.routers import draft_players, drafts, matches, players, rounds

app = FastAPI(title="Draft MTG API", description="API for managing MTG drafts", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(players.router)
app.include_router(drafts.router)
app.include_router(draft_players.router)
app.include_router(rounds.router)
app.include_router(matches.router)
app.include_router(users.router)
app.include_router(login.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to Draft MTG API"}
