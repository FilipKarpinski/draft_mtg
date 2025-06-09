from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.models import User
from app.auth.utils import get_current_active_user
from app.core.models import Draft, DraftPlayer, Match, Round
from app.core.schemas.drafts import DraftCreate, DraftFull, DraftList
from app.core.utils.drafts import calculate_points, populate_draft
from app.core.utils.pagination import PaginationParams, get_pagination_params
from app.db.database import get_db

router = APIRouter(prefix="/drafts", tags=["drafts"])


@router.post("/")
async def create_draft(
    draft: DraftCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_active_user)
) -> DraftFull:
    """
    Order of player ids is the order in which the players will play in first round, meaning
    1v2, 3v4, 5v6, etc.
    """
    try:
        db_draft = Draft(name=draft.name, date=draft.date)
        db.add(db_draft)
        await db.commit()
        await db.refresh(db_draft)

        for index, player_id in enumerate(draft.player_ids):
            draft_player = DraftPlayer(
                draft_id=db_draft.id,
                player_id=player_id,
                order=index + 1,
            )
            db.add(draft_player)

            await db.commit()
    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Draft name already exists or wrong player ids") from err

    # Reload with relationships
    stmt = select(Draft).options(selectinload(Draft.draft_players)).filter(Draft.id == db_draft.id)
    result = await db.execute(stmt)
    db_draft_with_players = result.scalar()
    if db_draft_with_players is None:
        raise HTTPException(status_code=500, detail="Failed to reload draft")

    try:
        await populate_draft(db_draft_with_players, db)
        # Load draft with all nested relationships like read_draft does
        stmt = (
            select(Draft)
            .options(
                selectinload(Draft.rounds).selectinload(Round.matches).selectinload(Match.player_1),
                selectinload(Draft.rounds).selectinload(Round.matches).selectinload(Match.player_2),
                selectinload(Draft.draft_players).selectinload(DraftPlayer.player),
            )
            .filter(Draft.id == db_draft.id)
        )

        result = await db.execute(stmt)
        db_draft_full = result.scalar()

        return DraftFull.model_validate(db_draft_full)
    except Exception as err:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Failed to populate draft") from err


@router.get("/{draft_id}")
async def read_draft(draft_id: int, db: AsyncSession = Depends(get_db)) -> DraftFull:
    # Load draft with all nested relationships
    stmt = (
        select(Draft)
        .options(
            selectinload(Draft.rounds).selectinload(Round.matches).selectinload(Match.player_1),
            selectinload(Draft.rounds).selectinload(Round.matches).selectinload(Match.player_2),
            selectinload(Draft.draft_players).selectinload(DraftPlayer.player),
        )
        .filter(Draft.id == draft_id)
    )

    result = await db.execute(stmt)
    db_draft = result.scalar()
    if db_draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    return DraftFull.model_validate(db_draft)


@router.get("/", response_model=list[DraftList])
async def list_drafts(
    pagination: PaginationParams = Depends(get_pagination_params), db: AsyncSession = Depends(get_db)
) -> Any:
    stmt = select(Draft).offset(pagination.skip).limit(pagination.limit)

    result = await db.execute(stmt)
    drafts = result.scalars().all()
    return drafts


@router.delete("/{draft_id}")
async def delete_draft(
    draft_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_active_user)
) -> dict[str, str]:
    result = await db.execute(select(Draft).filter(Draft.id == draft_id))
    db_draft = result.scalar()
    if db_draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")

    await db.delete(db_draft)
    await db.commit()
    return {"message": "Draft deleted successfully"}


@router.post("/{draft_id}/results")
async def get_results(draft_id: int, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    result = await db.execute(select(Draft).filter(Draft.id == draft_id))
    db_draft = result.scalar()
    if db_draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")

    await calculate_points(db_draft, db)

    return {"message": "Draft results calculated successfully"}
