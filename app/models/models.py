import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


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
        Enum(ElectionStatus),
        nullable=False,
        default=ElectionStatus.DRAFT,
    )

    merkle_root: Mapped[str | None] = mapped_column(String(255), nullable=True)

    starts_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    candidates: Mapped[list["Candidate"]] = relationship(
        back_populates="election",
        cascade="all, delete-orphan",
    )

    voter_tokens: Mapped[list["VoterToken"]] = relationship(
        back_populates="election",
        cascade="all, delete-orphan",
    )

    votes: Mapped[list["Vote"]] = relationship(
        back_populates="election",
        cascade="all, delete-orphan",
    )


class Candidate(Base):
    __tablename__: str = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    election_id: Mapped[int] = mapped_column(
        ForeignKey("elections.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    election: Mapped["Election"] = relationship(back_populates="candidates")

    votes: Mapped[list["Vote"]] = relationship(
        back_populates="candidate",
        cascade="all, delete-orphan",
    )


class VoterToken(Base):
    __tablename__: str = "voter_tokens"

    __table_args__: tuple = (
        UniqueConstraint(
            "election_id",
            "token_hash",
            name="uq_voter_tokens_election_token",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    election_id: Mapped[int] = mapped_column(
        ForeignKey("elections.id"),
        nullable=False,
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    merkle_index: Mapped[int] = mapped_column(Integer, nullable=False)
    merkle_path_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    label_for_admin: Mapped[str | None] = mapped_column(String(120), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    election: Mapped["Election"] = relationship(back_populates="voter_tokens")


class Vote(Base):
    __tablename__: str = "votes"

    __table_args__: tuple = (
        UniqueConstraint(
            "election_id",
            "nullifier_hash",
            name="uq_votes_election_nullifier",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    election_id: Mapped[int] = mapped_column(
        ForeignKey("elections.id"),
        nullable=False,
        index=True,
    )

    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id"),
        nullable=False,
        index=True,
    )

    nullifier_hash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    proof_json: Mapped[str] = mapped_column(Text, nullable=False)
    public_signals_json: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    election: Mapped["Election"] = relationship(back_populates="votes")
    candidate: Mapped["Candidate"] = relationship(back_populates="votes")
