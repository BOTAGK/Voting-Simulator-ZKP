from pydantic import BaseModel, ConfigDict, Field


class CandidateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None


class CandidateRead(BaseModel):
    id: int
    election_id: int
    name: str
    description: str | None

    model_config: ConfigDict = ConfigDict(from_attributes=True)


class CandidateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
