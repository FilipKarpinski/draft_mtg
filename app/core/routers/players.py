from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.utils import get_current_active_user
from app.core.models import Player
from app.core.schemas.players import PlayerCreate, PlayerSchema
from app.db.database import get_db

router = APIRouter(prefix="/players", tags=["players"])


@router.post("/")
async def create_player(
    player: PlayerCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_active_user)
) -> PlayerSchema:
    db_player = Player(name=player.name)
    db.add(db_player)
    await db.commit()
    await db.refresh(db_player)
    return PlayerSchema.model_validate(db_player)


@router.get("/", response_model=list[PlayerSchema])
async def list_players(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)) -> Any:
    result = await db.execute(select(Player).offset(skip).limit(limit))
    players = result.scalars().all()
    return players


@router.get("/{player_id}")
async def get_player(player_id: int, db: AsyncSession = Depends(get_db)) -> PlayerSchema:
    result = await db.execute(select(Player).filter(Player.id == player_id))
    player = result.scalar()
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return PlayerSchema.model_validate(player)


@router.put("/{player_id}")
async def update_player(
    player_id: int,
    player: PlayerCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> PlayerSchema:
    result = await db.execute(select(Player).filter(Player.id == player_id))
    db_player = result.scalar()
    if db_player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    db_player.name = player.name

    await db.commit()
    await db.refresh(db_player)
    return PlayerSchema.model_validate(db_player)


@router.delete("/{player_id}")
async def delete_player(
    player_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_active_user)
) -> dict[str, str]:
    result = await db.execute(select(Player).filter(Player.id == player_id))
    db_player = result.scalar()
    if db_player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    await db.delete(db_player)
    await db.commit()
    return {"message": "Player deleted successfully"}
