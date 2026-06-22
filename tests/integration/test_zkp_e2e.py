from app.schemas.voter_token import MerkleProofSchema, VoterTokenPackage
from app.services import zkp_service
from app.zkp.merkle import MerkleTree
from app.zkp.poseidon import poseidon_hash
from scripts import voter_client


def test_voter_client_generates_proof_verified_by_backend():
    election_id = 1
    token_secret = 123456

    token_hash = poseidon_hash([token_secret])
    tree = MerkleTree([token_hash], depth=10)
    proof = tree.get_proof(0)

    voter_package = VoterTokenPackage(
        election_id=election_id,
        token_secret=str(token_secret),
        merkle_root=str(tree.root),
        merkle_index=0,
        merkle_proof=MerkleProofSchema(
            siblings=[str(sibling) for sibling in proof.siblings],
            path_indices=proof.path_indices,
        ),
    )

    vote_payload = voter_client.build_vote_payload(
        voter_package,
        candidate_id=1,
    )

    assert zkp_service.verify_proof(
        vote_payload.proof,
        vote_payload.public_signals,
    )