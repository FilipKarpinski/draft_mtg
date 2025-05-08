from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.utils import get_current_active_user
from app.core.models import Draft, DraftPlayer
from app.core.schemas.draft_players import DraftPlayerSchema, DraftPlayerSetOrdersSchema
from app.core.schemas.drafts import DraftCreate, DraftSchema
from app.core.schemas.matches import MatchSchema
from app.core.utils.drafts import calculate_final_places, generate_matches
from app.db.database import get_db

router = APIRouter(prefix="/drafts", tags=["drafts"])


@router.post("/")
async def create_draft(
    draft: DraftCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_active_user)
) -> DraftSchema:
    db_draft = Draft(
        name=draft.name,
    )
    db.add(db_draft)
    await db.commit()
    await db.refresh(db_draft)

    for player_id in draft.player_ids:
        draft_player = DraftPlayer(
            draft_id=db_draft.id,
            player_id=player_id,
        )
        db.add(draft_player)

    await db.commit()
    await db.refresh(db_draft)
    return db_draft


@router.get("/{draft_id}")
async def read_draft(draft_id: int, db: AsyncSession = Depends(get_db)) -> DraftSchema:
    result = await db.execute(select(Draft).filter(Draft.id == draft_id))
    db_draft = result.scalar()
    if db_draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    return db_draft


@router.get("/", response_model=list[DraftSchema])
async def list_drafts(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)) -> Any:
    result = await db.execute(select(Draft).offset(skip).limit(limit))
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
        setattr(db_draft, field, value)

    await db.commit()
    await db.refresh(db_draft)
    return db_draft


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


@router.get("/{draft_id}/matches", response_model=list[MatchSchema])
async def list_draft_matches(draft_id: int, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)) -> Any:
    result = await db.execute(select(Draft).filter(Draft.id == draft_id))
    db_draft = result.scalar()
    if db_draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")

    matches = db_draft.matches[skip : skip + limit]
    return matches


@router.get("/{draft_id}/players", response_model=list[DraftPlayerSchema])
async def list_draft_players(draft_id: int, db: AsyncSession = Depends(get_db)) -> Any:
    result = await db.execute(select(Draft).filter(Draft.id == draft_id))
    db_draft = result.scalar()
    if db_draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")

    players = db_draft.draft_players
    return players


@router.post("/{draft_id}/generate_matches", response_model=list[MatchSchema])
async def generate_draft_matches(draft_id: int, db: AsyncSession = Depends(get_db)) -> Any:
    """
    Generate the matches for the draft.
    The matches are generated based on order of the players in the draft.
    You can set the order of the players in the draft using the set_draft_players_orders endpoint.
    """
    result = await db.execute(select(Draft).filter(Draft.id == draft_id))
    db_draft = result.scalar()
    if db_draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")

    if len(db_draft.matches) > 0:
        raise HTTPException(status_code=400, detail="Draft already has matches generated")

    matches = await generate_matches(db_draft, db)
    return matches


@router.put("/{draft_id}/players/orders")
async def set_draft_players_orders(
    draft_id: int,
    draft_player_set_orders: DraftPlayerSetOrdersSchema,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> DraftSchema:
    """
    Set the order of the players in the draft.
    The order is a dictionary where the key is the player id and the value is the order.
    Example:
    {
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
    }
    """
    result = await db.execute(select(Draft).filter(Draft.id == draft_id))
    db_draft = result.scalar()
    if db_draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")

    for player_id, order in draft_player_set_orders.player_orders.items():
        result = await db.execute(
            select(DraftPlayer).filter(DraftPlayer.draft_id == draft_id, DraftPlayer.player_id == player_id)
        )
        draft_player = result.scalar()
        if draft_player is None:
            raise HTTPException(status_code=404, detail="Draft player not found")
        draft_player.order = order

    await db.commit()
    await db.refresh(db_draft)
    return db_draft


@router.get("/{draft_id}/results", response_model=list[DraftPlayerSchema])
async def get_results(draft_id: int, db: AsyncSession = Depends(get_db)) -> Any:
    result = await db.execute(select(Draft).filter(Draft.id == draft_id))
    db_draft = result.scalar()
    if db_draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")

    await calculate_final_places(db_draft, db)

    players = sorted(db_draft.draft_players, key=lambda x: x.final_place or float("inf"))
    return players
