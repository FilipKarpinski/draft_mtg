from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.models import User
from app.auth.utils import get_current_active_user
from app.core.models import Draft, DraftPlayer, Match, Round
from app.core.schemas.draft_players import DraftPlayerSchema
from app.core.schemas.drafts import DraftCreate, DraftSchema
from app.core.schemas.matches import MatchSchema
from app.core.schemas.rounds import RoundSchema
from app.core.utils.drafts import calculate_final_places, generate_matches
from app.db.database import get_db

router = APIRouter(prefix="/drafts", tags=["drafts"])


@router.post("/")
async def create_draft(
    draft: DraftCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_active_user)
) -> int:
    """
    Order of player ids is the order in which the players will play in first round, meaning
    1v2, 3v4, 5v6, etc.
    """
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

    # Reload with relationships
    stmt = select(Draft).options(selectinload(Draft.draft_players)).filter(Draft.id == db_draft.id)
    result = await db.execute(stmt)
    db_draft_with_players = result.scalar()
    if db_draft_with_players is None:
        raise HTTPException(status_code=500, detail="Failed to reload draft")

    await generate_matches(db_draft_with_players, db)

    return db_draft.id


@router.get("/{draft_id}")
async def read_draft(draft_id: int, db: AsyncSession = Depends(get_db)) -> DraftSchema:
    # Load draft with all nested relationships
    stmt = (
        select(Draft)
        .options(
            selectinload(Draft.rounds).selectinload(Round.matches).selectinload(Match.player_1),
            selectinload(Draft.rounds).selectinload(Round.matches).selectinload(Match.player_2),
            selectinload(Draft.draft_players),
        )
        .filter(Draft.id == draft_id)
    )

    result = await db.execute(stmt)
    db_draft = result.scalar()
    if db_draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    return DraftSchema.model_validate(db_draft)


@router.get("/", response_model=list[DraftSchema])
async def list_drafts(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)) -> Any:
    # Load drafts with all nested relationships
    stmt = (
        select(Draft)
        .options(
            selectinload(Draft.rounds).selectinload(Round.matches).selectinload(Match.player_1),
            selectinload(Draft.rounds).selectinload(Round.matches).selectinload(Match.player_2),
            selectinload(Draft.draft_players),
        )
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(stmt)
    drafts = result.scalars().all()
    return drafts


@router.put("/{draft_id}")
async def update_draft(
    draft_id: int,
    draft: DraftCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> DraftSchema:
    result = await db.execute(select(Draft).filter(Draft.id == draft_id))
    db_draft = result.scalar()
    if db_draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")

    for field, value in draft.model_dump().items():
        if field != "player_ids":  # Skip player_ids as it's not a direct field
            setattr(db_draft, field, value)

    await db.commit()
    await db.refresh(db_draft)
    return DraftSchema.model_validate(db_draft)


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


@router.get("/{draft_id}/rounds", response_model=list[RoundSchema])
async def list_draft_rounds(draft_id: int, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)) -> Any:
    result = await db.execute(select(Draft).filter(Draft.id == draft_id))
    db_draft = result.scalar()
    if db_draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")

    rounds = db_draft.rounds[skip : skip + limit]
    return rounds


@router.get("/{draft_id}/matches", response_model=list[MatchSchema])
async def list_draft_matches(draft_id: int, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)) -> Any:
    result = await db.execute(select(Draft).filter(Draft.id == draft_id))
    db_draft = result.scalar()
    if db_draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")

    # Collect all matches from all rounds
    matches = []
    for round_obj in db_draft.rounds:
        matches.extend(round_obj.matches)

    return matches[skip : skip + limit]


@router.get("/{draft_id}/players", response_model=list[DraftPlayerSchema])
async def list_draft_players(draft_id: int, db: AsyncSession = Depends(get_db)) -> Any:
    result = await db.execute(select(Draft).filter(Draft.id == draft_id))
    db_draft = result.scalar()
    if db_draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")

    players = db_draft.draft_players
    return players


@router.get("/{draft_id}/results", response_model=list[DraftPlayerSchema])
async def get_results(draft_id: int, db: AsyncSession = Depends(get_db)) -> Any:
    result = await db.execute(select(Draft).filter(Draft.id == draft_id))
    db_draft = result.scalar()
    if db_draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")

    await calculate_final_places(db_draft, db)

    players = sorted(db_draft.draft_players, key=lambda x: x.final_place or float("inf"))
    return players
