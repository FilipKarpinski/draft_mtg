from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.schemas import UserBase, UserCreate
from app.auth.utils import get_current_active_user, get_current_admin_user, get_password_hash
from app.db.database import get_db

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/")
def create_user(user: UserCreate, db: Session = Depends(get_db)) -> UserBase:
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password),
        is_active=False,  # User starts as inactive by default
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/", response_model=list[UserBase])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Any:
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)) -> UserBase:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}")
def update_user(
    user_id: int, user: UserCreate, db: Session = Depends(get_db), _: User = Depends(get_current_admin_user)
) -> UserBase:
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.username = user.username
    db_user.email = user.email
    db_user.hashed_password = get_password_hash(user.password)

    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/{user_id}")
def delete_user(
    user_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin_user)
) -> dict[str, str]:
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(db_user)
    db.commit()
    return {"message": "User deleted successfully"}
