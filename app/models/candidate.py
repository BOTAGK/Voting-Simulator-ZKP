from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.election import Election
    from app.models.vote import Vote


class Candidate(Base):
    __tablename__: str = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    election_id: Mapped[int] = mapped_column(
        ForeignKey("elections.id"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    election: Mapped["Election"] = relationship(
        back_populates="candidates",
    )

    votes: Mapped[list["Vote"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )
