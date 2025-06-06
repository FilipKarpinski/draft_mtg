from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.utils import get_current_active_user
from app.core.models import DraftPlayer
from app.core.schemas.draft_players import DraftPlayerEdit, DraftPlayerSchema
from app.db.database import get_db

router = APIRouter(prefix="/draft-players", tags=["draft-players"])


@router.put("/{draft_id}/{draft_player_id}")
async def update_draft_player(
    draft_id: int,
    player_id: int,
    draft_player_edit: DraftPlayerEdit,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> DraftPlayerSchema:
    """Update a draft player's information."""
    # Find the draft player
    stmt = select(DraftPlayer).filter(DraftPlayer.draft_id == draft_id, DraftPlayer.player_id == player_id)
    result = await db.execute(stmt)
    db_draft_player = result.scalar()

    if db_draft_player is None:
        raise HTTPException(status_code=404, detail="Draft player not found")

    # Update the fields from the edit schema
    for field, value in draft_player_edit.model_dump(exclude_unset=True).items():
        setattr(db_draft_player, field, value)

    await db.commit()
    await db.refresh(db_draft_player)

    return DraftPlayerSchema.model_validate(db_draft_player)
