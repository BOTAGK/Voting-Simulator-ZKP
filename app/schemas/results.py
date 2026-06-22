from pydantic import BaseModel


class CandidateResultRead(BaseModel):
    candidate_id: int
    candidate_name: str
    votes: int


class ElectionResultsRead(BaseModel):
    election_id: int
    election_name: str
    status: str
    total_votes: int
    total_tokens: int
    turnout: float
    results: list[CandidateResultRead]
