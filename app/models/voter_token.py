from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.election import Election


class VoterToken(Base):
    __tablename__: str = "voter_tokens"

    __table_args__: tuple = (
        UniqueConstraint(
            "election_id", 
            "token_hash", 
            name="uq_voter_tokens_election_token"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

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
