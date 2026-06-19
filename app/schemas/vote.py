from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VoteCreate(BaseModel):
    candidate_id: int
    nullifier_hash: str = Field(min_length=1, max_length=255)
    proof_json: str = Field(min_length=1)
    public_signals_json: str = Field(min_length=1)


class VoteRead(BaseModel):
    id: int
    election_id: int
    candidate_id: int
    nullifier_hash: str
    created_at: datetime

    model_config: ConfigDict = ConfigDict(from_attributes=True)


class VoteAuditRead(BaseModel):
    id: int
    election_id: int
    candidate_id: int
    nullifier_hash: str
    proof_json: str
    public_signals_json: str
    created_at: datetime

    model_config: ConfigDict = ConfigDict(from_attributes=True)


class VoteAccepted(BaseModel):
    vote_id: int
    election_id: int
    candidate_id: int
    message: str = "Vote accepted"
