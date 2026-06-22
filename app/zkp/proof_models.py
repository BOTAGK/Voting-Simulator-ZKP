from pydantic import BaseModel


class PublicSignals(BaseModel):
    election_id: int
    merkle_root: str
    nullifier_hash: str


class VoteCircuitInput(BaseModel):
    token_secret: str
    merkle_siblings: list[str]
    merkle_path_indices: list[str]
    election_id: str
    merkle_root: str
