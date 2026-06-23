from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MerkleProofSchema(BaseModel):
    siblings: list[str]
    path_indices: list[Literal[0, 1]]


class VoterTokenGenerateRequest(BaseModel):
    count: int = Field(gt=0, le=1000)
    label_prefix: str | None = Field(default=None, max_length=80)


class VoterTokenRead(BaseModel):
    id: int
    election_id: int
    token_hash: str
    merkle_index: int
    merkle_path_json: str | None
    label_for_admin: str | None
    created_at: datetime

    model_config: ConfigDict = ConfigDict(from_attributes=True)


class VoterTokenPackage(BaseModel):
    election_id: int
    token_secret: str
    merkle_root: str
    merkle_index: int
    merkle_proof: MerkleProofSchema
