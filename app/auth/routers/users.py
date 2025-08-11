from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.schemas import UserBase, UserCreate
from app.auth.utils import get_current_active_user, get_current_admin_user, get_current_user, get_password_hash
from app.core.utils.pagination import PaginationParams, get_pagination_params
from app.db.database import get_db

router = APIRouter(prefix="/users", tags=["users"])


@router.post("")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)) -> UserBase:
    db_user = User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        is_active=False,
        is_admin=False,
    )
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
        return UserBase.model_validate(db_user)
    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered") from err


@router.get("", response_model=list[UserBase])
async def list_users(
    pagination: PaginationParams = Depends(get_pagination_params),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Any:
    result = await db.execute(select(User).offset(pagination.skip).limit(pagination.limit))
    users = result.scalars().all()
    return users


@router.get("/me", response_model=UserBase)
async def get_me(current_user: User = Depends(get_current_user)) -> UserBase:
    """
    Get details of the currently authenticated user.
    """
    return UserBase.model_validate(current_user)


@router.get("/{user_id}")
async def get_user(
    user_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_active_user)
) -> UserBase:
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserBase.model_validate(user)


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserBase:
    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalar()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    db_user.email = user.email
    db_user.hashed_password = get_password_hash(user.password)

    await db.commit()
    await db.refresh(db_user)
    return UserBase.model_validate(db_user)


@router.post("/{user_id}/promote-to-admin")
async def promote_user_to_admin(
    user_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_admin_user)
) -> dict[str, str]:
    """Promote an existing user to admin. Requires admin privileges."""
    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalar()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.is_admin = True
    await db.commit()
    return {"message": "User promoted to admin successfully"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_admin_user)
) -> dict[str, str]:
    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalar()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(db_user)
    await db.commit()
    return {"message": "User deleted successfully"}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_admin_user)
) -> dict[str, str]:
    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalar()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.is_active = True
    await db.commit()
    return {"message": "User activated successfully"}
