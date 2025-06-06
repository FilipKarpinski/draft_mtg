from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.utils import get_current_active_user
from app.core.models import Match
from app.core.schemas.matches import MatchScoreUpdate
from app.db.database import get_db

router = APIRouter(prefix="/matches", tags=["matches"])


@router.put("/{match_id}")
async def set_score(
    match_id: int,
    match_update: MatchScoreUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> dict[str, str]:
    stmt = select(Match).filter(Match.id == match_id)
    result = await db.execute(stmt)
    db_match = result.scalar()
    if db_match is None:
        raise HTTPException(status_code=404, detail="Match not found")

    db_match.score = match_update.score

    await db.commit()
    return {"message": "Match score updated successfully"}
