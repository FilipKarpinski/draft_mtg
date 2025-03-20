from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.models import Player
from app.core.schemas import PlayerCreate, PlayerSchema
from app.db.database import get_db

router = APIRouter(prefix="/players", tags=["players"])


@router.post("/")
def create_player(player: PlayerCreate, db: Session = Depends(get_db)) -> PlayerSchema:
    db_player = Player(name=player.name, profile_picture_path=player.profile_picture_path or "")
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player


@router.get("/", response_model=list[PlayerSchema])
def list_players(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> Any:
    players = db.query(Player).offset(skip).limit(limit).all()
    return players


@router.get("/{player_id}")
def get_player(player_id: int, db: Session = Depends(get_db)) -> PlayerSchema:
    player = db.query(Player).filter(Player.id == player_id).first()
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


@router.put("/{player_id}")
def update_player(player_id: int, player: PlayerCreate, db: Session = Depends(get_db)) -> PlayerSchema:
    db_player = db.query(Player).filter(Player.id == player_id).first()
    if db_player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    db_player.name = player.name
    db_player.profile_picture_path = player.profile_picture_path or ""

    db.commit()
    db.refresh(db_player)
    return db_player


@router.delete("/{player_id}")
def delete_player(player_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    db_player = db.query(Player).filter(Player.id == player_id).first()
    if db_player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    db.delete(db_player)
    db.commit()
    return {"message": "Player deleted successfully"}
