from datetime import datetime
from enum import Enum

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


class MatchResult(str, Enum):
    PLAYER_1_FULL_WIN = "2-0"
    PLAYER_1_WIN = "2-1"
    PLAYER_2_WIN = "1-2"
    PLAYER_2_FULL_WIN = "0-2"


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

    draft_players = relationship("DraftPlayer", back_populates="player")


# pylint: disable=not-callable
class Draft(Base):
    __tablename__ = "drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    matches = relationship("Match", back_populates="draft", cascade="all, delete-orphan")
    draft_players = relationship("DraftPlayer", back_populates="draft", cascade="all, delete-orphan")


# pylint: disable=not-callable
class DraftPlayer(Base):
    __tablename__ = "draft_players"

    draft_id: Mapped[int] = mapped_column(Integer, ForeignKey("drafts.id"), primary_key=True)
    player_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"), primary_key=True)
    final_place: Mapped[int] = mapped_column(Integer, nullable=True)
    order: Mapped[int] = mapped_column(Integer, nullable=True)
    draft = relationship("Draft", back_populates="draft_players")
    player = relationship("Player", back_populates="draft_players")


# pylint: disable=not-callable
class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    round: Mapped[int] = mapped_column(Integer)
    player_1_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"))
    player_2_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"))
    score: Mapped[str] = mapped_column(String, nullable=True)
    draft_id: Mapped[int] = mapped_column(Integer, ForeignKey("drafts.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Add check constraint to ensure player_1_id != player_2_id and valid scores
    __table_args__ = (
        CheckConstraint("player_1_id != player_2_id", name="check_different_players"),
        CheckConstraint(f"score IN ({', '.join(repr(v.value) for v in MatchResult)})", name="check_valid_scores"),
    )

    draft = relationship("Draft", back_populates="matches")
    player_1 = relationship("Player", back_populates="matches_as_player_1", foreign_keys=[player_1_id])
    player_2 = relationship("Player", back_populates="matches_as_player_2", foreign_keys=[player_2_id])
