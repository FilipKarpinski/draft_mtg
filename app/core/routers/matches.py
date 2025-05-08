from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.utils import get_current_active_user
from app.core.models import POINTS_MAP, Match, MatchResult
from app.core.schemas.matches import MatchSchema
from app.db.database import get_db

router = APIRouter(prefix="/matches", tags=["matches"])


@router.put("/{match_id}")
async def set_score(
    match_id: int,
    score: MatchResult,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> MatchSchema:
    result = await db.execute(select(Match).filter(Match.id == match_id))
    db_match = result.scalar_one_or_none()
    if db_match is None:
        raise HTTPException(status_code=404, detail="Match not found")

    db_match.score = score
    player_1_points, player_2_points = POINTS_MAP[score]
    db_match.draft.draft_players[db_match.player_1_id].points += player_1_points
    db_match.draft.draft_players[db_match.player_2_id].points += player_2_points

    await db.commit()
    await db.refresh(db_match)
    return db_match
