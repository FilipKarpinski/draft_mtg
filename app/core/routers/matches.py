from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.models import User
from app.auth.utils import get_current_active_user
from app.core.models import POINTS_MAP, Match, MatchResult, Round
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
    # Load match with round and draft relationships
    stmt = (
        select(Match)
        .options(
            selectinload(Match.round).selectinload(Round.draft),
            selectinload(Match.player_1),
            selectinload(Match.player_2),
        )
        .filter(Match.id == match_id)
    )
    result = await db.execute(stmt)
    db_match = result.scalar()
    if db_match is None:
        raise HTTPException(status_code=404, detail="Match not found")

    db_match.score = score
    player_1_points, player_2_points = POINTS_MAP[score]

    # Find the draft players and update their points
    draft = db_match.round.draft
    for draft_player in draft.draft_players:
        if draft_player.player_id == db_match.player_1_id:
            draft_player.points += player_1_points
        elif draft_player.player_id == db_match.player_2_id:
            draft_player.points += player_2_points

    await db.commit()
    await db.refresh(db_match)
    return MatchSchema.model_validate(db_match)
