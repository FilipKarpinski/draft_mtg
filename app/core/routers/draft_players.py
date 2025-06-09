from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.models import User
from app.auth.utils import get_current_active_user
from app.core.models import DraftPlayer
from app.core.schemas.draft_players import DraftPlayerSchema, DraftPlayerUpdate
from app.db.database import get_db

router = APIRouter(prefix="/draft-players", tags=["draft-players"])


@router.patch("/{draft_id}/{player_id}")
async def update_draft_player(
    draft_id: int,
    player_id: int,
    update_data: DraftPlayerUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> DraftPlayerSchema:
    """Update a draft player's information with partial data."""
    # Find the draft player
    stmt = select(DraftPlayer).filter(DraftPlayer.draft_id == draft_id, DraftPlayer.player_id == player_id)
    result = await db.execute(stmt)
    db_draft_player = result.scalar()

    if db_draft_player is None:
        raise HTTPException(status_code=404, detail="Draft player not found")

    # Update only the fields that were provided (not None)
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(db_draft_player, field, value)

    await db.commit()
    await db.refresh(db_draft_player)

    # Reload with player relationship to avoid MissingGreenlet error
    stmt = (
        select(DraftPlayer)
        .options(selectinload(DraftPlayer.player))
        .filter(DraftPlayer.draft_id == draft_id, DraftPlayer.player_id == player_id)
    )
    result = await db.execute(stmt)
    db_draft_player_with_player = result.scalar()

    return DraftPlayerSchema.model_validate(db_draft_player_with_player)
