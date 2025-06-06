from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import Match, Round
from app.core.schemas.matches import MatchSchema
from app.core.schemas.rounds import RoundSchema
from app.db.database import get_db

router = APIRouter(prefix="/rounds", tags=["rounds"])


@router.get("/{round_id}")
async def read_round(round_id: int, db: AsyncSession = Depends(get_db)) -> RoundSchema:
    stmt = (
        select(Round)
        .options(
            selectinload(Round.matches).selectinload(Match.player_1),
            selectinload(Round.matches).selectinload(Match.player_2),
        )
        .filter(Round.id == round_id)
    )

    result = await db.execute(stmt)
    db_round = result.scalar()
    if db_round is None:
        raise HTTPException(status_code=404, detail="Round not found")
    return RoundSchema.model_validate(db_round)


@router.get("/{round_id}/matches", response_model=list[MatchSchema])
async def list_round_matches(round_id: int, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)) -> Any:
    result = await db.execute(select(Round).filter(Round.id == round_id))
    db_round = result.scalar()
    if db_round is None:
        raise HTTPException(status_code=404, detail="Round not found")

    matches = db_round.matches[skip : skip + limit]
    return matches
