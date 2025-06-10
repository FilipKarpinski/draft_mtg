from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.utils import get_current_active_user, get_current_admin_user
from app.core.models import Draft, DraftPlayer, Match, Player
from app.core.schemas.players import PlayerCreate, PlayerSchema
from app.core.utils.pagination import PaginationParams, get_pagination_params
from app.db.database import get_db

router = APIRouter(prefix="/players", tags=["players"])


@router.post("")
async def create_player(
    player: PlayerCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_active_user)
) -> PlayerSchema:
    db_player = Player(name=player.name)
    db.add(db_player)
    try:
        await db.commit()
        await db.refresh(db_player)
        return PlayerSchema.model_validate(db_player)
    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Player name already exists") from err


@router.get("", response_model=list[PlayerSchema])
async def list_players(
    pagination: PaginationParams = Depends(get_pagination_params), db: AsyncSession = Depends(get_db)
) -> Any:
    result = await db.execute(select(Player).offset(pagination.skip).limit(pagination.limit))
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

    try:
        await db.commit()
        await db.refresh(db_player)
        return PlayerSchema.model_validate(db_player)
    except IntegrityError as e:
        await db.rollback()
        if "unique constraint" in str(e).lower() or "duplicate key" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail=f"Player with name '{player.name}' already exists. Please choose a different name.",
            ) from e
        raise HTTPException(status_code=400, detail="Database error occurred") from e


@router.delete("/{player_id}")
async def delete_player(
    player_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_admin_user)
) -> dict[str, str]:
    result = await db.execute(select(Player).filter(Player.id == player_id))
    db_player = result.scalar()
    if db_player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    # Check if player is referenced in any draft_players
    draft_players_result = await db.execute(select(DraftPlayer).filter(DraftPlayer.player_id == player_id))
    draft_players = draft_players_result.scalars().all()

    if draft_players:
        draft_names = []
        for dp in draft_players:
            draft_result = await db.execute(select(Draft).filter(Draft.id == dp.draft_id))
            draft = draft_result.scalar()
            if draft:
                draft_names.append(draft.name)

        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete player '{db_player.name}' because they are participating in drafts: {', '.join(draft_names)}. Remove them from these drafts first.",
        )

    # Check if player is referenced in any matches
    matches_result = await db.execute(
        select(Match).filter((Match.player_1_id == player_id) | (Match.player_2_id == player_id))
    )
    matches = matches_result.scalars().all()

    if matches:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete player '{db_player.name}' because they have match history. This player has played {len(matches)} matches.",
        )

    # If no foreign key constraints, proceed with deletion
    await db.delete(db_player)
    await db.commit()
    return {"message": "Player deleted successfully"}


@router.get("/{player_id}/placements")
async def get_player_placements(player_id: int, db: AsyncSession = Depends(get_db)) -> dict[int, int]:
    result = await db.execute(select(DraftPlayer).filter(DraftPlayer.player_id == player_id))
    players_drafts = result.scalars().all()
    if players_drafts is None:
        raise HTTPException(status_code=404, detail="Player not found")

    placement_dict: dict[int, int] = defaultdict(int)
    for draft in players_drafts:
        if draft.final_place is not None:
            placement_dict[draft.final_place] += 1
    return placement_dict
