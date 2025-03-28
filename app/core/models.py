from datetime import datetime

from sqlalchemy import (  # pylint: disable=no-name-in-module
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import (  # pylint: disable=no-name-in-module
    Mapped,
    mapped_column,
    relationship,
)

from app.db.database import Base


# pylint: disable=not-callable
class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    profile_picture_path: Mapped[str] = mapped_column(String, index=True, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Add relationships for matches
    matches_as_player_1 = relationship("Match", back_populates="player_1", foreign_keys="Match.player_1_id")
    matches_as_player_2 = relationship("Match", back_populates="player_2", foreign_keys="Match.player_2_id")


# pylint: disable=not-callable
class Draft(Base):
    __tablename__ = "drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    draft_date: Mapped[datetime] = mapped_column(DateTime, index=True, default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    matches = relationship("Match", back_populates="draft")


# pylint: disable=not-callable
class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    player_1_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"))
    player_2_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"))
    score_1: Mapped[int] = mapped_column(Integer)
    score_2: Mapped[int] = mapped_column(Integer)
    draft_id: Mapped[int] = mapped_column(Integer, ForeignKey("drafts.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Add check constraint to ensure player_1_id != player_2_id
    __table_args__ = (CheckConstraint("player_1_id != player_2_id", name="check_different_players"),)

    draft = relationship("Draft", back_populates="matches")
    player_1 = relationship("Player", back_populates="matches_as_player_1", foreign_keys=[player_1_id])
    player_2 = relationship("Player", back_populates="matches_as_player_2", foreign_keys=[player_2_id])
