from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.models import Draft
from app.core.schemas import DraftCreate, DraftSchema
from app.db.database import get_db

router = APIRouter(prefix="/drafts", tags=["drafts"])


@router.post("/")
def create_draft(draft: DraftCreate, db: Session = Depends(get_db)) -> DraftSchema:
    db_draft = Draft(
        player_id=draft.player_id,
        draft_date=draft.draft_date,
    )
    db.add(db_draft)
    db.commit()
    db.refresh(db_draft)
    return db_draft


@router.get("/{draft_id}")
def read_draft(draft_id: int, db: Session = Depends(get_db)) -> DraftSchema:
    db_draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if db_draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    return db_draft


@router.get("/", response_model=list[DraftSchema])
def list_drafts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> Any:
    drafts: list[Draft] = db.query(Draft).offset(skip).limit(limit).all()
    return drafts


@router.put("/{draft_id}")
def update_draft(draft_id: int, draft: DraftCreate, db: Session = Depends(get_db)) -> DraftSchema:
    db_draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if db_draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")

    for field, value in draft.model_dump().items():
        setattr(db_draft, field, value)

    db.commit()
    db.refresh(db_draft)
    return db_draft


@router.delete("/{draft_id}")
def delete_draft(draft_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    db_draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if db_draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")

    db.delete(db_draft)
    db.commit()
    return {"message": "Draft deleted successfully"}
