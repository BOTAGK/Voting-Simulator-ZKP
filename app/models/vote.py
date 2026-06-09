from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


if TYPE_CHECKING:
    from app.models.candidate import Candidate
    from app.models.election import Election
    

class Vote(Base):
    __tablename__: str = "votes"

    __table_args__: tuple = (
        UniqueConstraint(
            "election_id", 
            "nullifier_hash", 
            name="uq_votes_election_nullifier"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    election_id: Mapped[int] = mapped_column(
        ForeignKey("elections.id"), nullable=False, index=True
    )

    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id"), nullable=False, index=True
    )

    nullifier_hash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    proof_json: Mapped[str] = mapped_column(Text, nullable=False)
    public_signals_json: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    election: Mapped["Election"] = relationship(
        back_populates="votes",
    )

    candidate: Mapped["Candidate"] = relationship(
        back_populates="votes",
    )
