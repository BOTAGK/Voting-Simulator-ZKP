from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import ElectionStatus


class ElectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class ElectionRead(BaseModel):
    id: int
    name: str
    description: str | None
    status: ElectionStatus
    merkle_root: str | None
    starts_at: datetime | None
    ends_at: datetime | None
    created_at: datetime

    model_config: ConfigDict = ConfigDict(from_attributes=True)


class ElectionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
