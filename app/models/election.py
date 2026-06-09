import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.candidate import Candidate
    from app.models.vote import Vote
    from app.models.voter_token import VoterToken


class ElectionStatus(str, enum.Enum):
    DRAFT: str = "draft"
    ACTIVE: str = "active"
    CLOSED: str = "closed"


class Election(Base):
    __tablename__: str = "elections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[ElectionStatus] = mapped_column(
        Enum(ElectionStatus), nullable=False, default=ElectionStatus.DRAFT
    )

    merkle_root: Mapped[str | None] = mapped_column(String(255), nullable=True)

    starts_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    candidates: Mapped[list["Candidate"]] = relationship(
        back_populates="election", cascade="all, delete-orphan"
    )

    voter_tokens: Mapped[list["VoterToken"]] = relationship(
        back_populates="election", cascade="all, delete-orphan"
    )

    votes: Mapped[list["Vote"]] = relationship(
        back_populates="election", cascade="all, delete-orphan"
    )
