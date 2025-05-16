# pylint: disable=unsubscriptable-object,not-callable
from datetime import datetime

from sqlalchemy import (  # pylint: disable=no-name-in-module
    Boolean,
    DateTime,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column  # pylint: disable=no-name-in-module

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    hashed_password: Mapped[str] = mapped_column(String(128))
    email: Mapped[str] = mapped_column(String, index=True, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
