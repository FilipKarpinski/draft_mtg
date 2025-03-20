from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.utils import get_current_active_user
from app.core.models import Match
from app.core.schemas import MatchCreate, MatchSchema
from app.db.database import get_db

router = APIRouter(prefix="/matches", tags=["matches"])


@router.post("/")
def create_match(
    match: MatchCreate, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)
) -> MatchSchema:
    db_match = Match(
        player_1_id=match.player_1_id,
        player_2_id=match.player_2_id,
        score_1=match.score_1,
        score_2=match.score_2,
        draft_id=match.draft_id,
    )
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match


@router.get("/{match_id}")
def read_match(match_id: int, db: Session = Depends(get_db)) -> MatchSchema:
    db_match = db.query(Match).filter(Match.id == match_id).first()
    if db_match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    return db_match


@router.get("/", response_model=list[MatchSchema])
def list_matches(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> Any:
    matches: list[Match] = db.query(Match).offset(skip).limit(limit).all()
    return matches


@router.put("/{match_id}")
def update_match(
    match_id: int,
    match: MatchSchema,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> MatchSchema:
    db_match = db.query(Match).filter(Match.id == match_id).first()
    if db_match is None:
        raise HTTPException(status_code=404, detail="Match not found")

    for field, value in match.dict(exclude_unset=True).items():
        setattr(db_match, field, value)

    db.commit()
    db.refresh(db_match)
    return db_match


@router.delete("/{match_id}")
def delete_match(
    match_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)
) -> dict[str, str]:
    db_match = db.query(Match).filter(Match.id == match_id).first()
    if db_match is None:
        raise HTTPException(status_code=404, detail="Match not found")

    db.delete(db_match)
    db.commit()
    return {"message": "Match deleted successfully"}
