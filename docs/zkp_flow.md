# ZKP Flow

The project uses a Circom circuit and Groth16 proofs to let a voter prove eligibility without sending the private token secret to the backend.

## Demonstration Scope

This is an educational implementation. The current circuit uses:

```text
VoteEligibility(10)
```

This means the Merkle proof depth is 10 and the tree capacity is:

```text
2^10 = 1024 leaves
```

If only 10 voter tokens are generated, the remaining leaves are padded with `0`. A production-scale election would need a larger depth, a more optimized tree implementation, and a complete security review.

## Token Generation

The administrator generates voter token packages for a draft election.

For each voter:

1. Generate a private `token_secret`.
2. Compute:

   ```text
   token_hash = Poseidon(token_secret)
   ```

3. Build a Merkle tree from all token hashes.
4. Store only public token metadata in the database:

   ```text
   token_hash
   merkle_index
   merkle_path_json
   ```

5. Return a one-time `VoterTokenPackage` containing:

   ```text
   token_secret
   merkle_root
   merkle_index
   merkle_proof
   ```

The `token_secret` is not stored in the database.

## Vote Circuit

The circuit proves three facts:

1. The voter knows `token_secret`.
2. `Poseidon(token_secret)` is included in the Merkle tree with root `merkle_root`.
3. `Poseidon(token_secret, election_id)` equals `nullifier_hash`.

Public signals:

```text
election_id
merkle_root
nullifier_hash
```

Private witness values:

```text
token_secret
merkle_siblings
merkle_path_indices
```

## Witness

The witness is the full set of values that satisfies the circuit. It includes private data and is generated locally by snarkjs from circuit input. In the browser flow, this happens on the voter's device through `snarkjs.groth16.fullProve`. The witness is not sent to the backend.

## Proof

The proof is generated from:

```text
witness + vote_eligibility_final.zkey
```

The backend receives:

```text
proof
public_signals
candidate_id
nullifier_hash
```

The backend does not receive:

```text
token_secret
merkle_siblings
merkle_path_indices
```

The repository also contains `scripts/voter_client.py`, which performs the same proof-building flow from the command line for tests and demos.

## Backend Verification

The vote endpoint performs these checks:

1. Election exists and is `active`.
2. Candidate belongs to the election.
3. Public signals match the submitted vote data and stored election Merkle root.
4. No existing vote has the same `(election_id, nullifier_hash)`.
5. `snarkjs groth16 verify` accepts the proof using `verification_key.json`.

Only after these checks does the backend store the vote.

## Demo Seed Notes

`scripts/seed_demo.py` creates:

- one draft election,
- one active election with a few demo votes,
- one closed election with historical demo results.

Demo votes inserted by the seed script contain real nullifier hashes, so already-used demo token packages are blocked by duplicate-nullifier logic. Their `proof_json` values are marked as demo data because the seed script is intended to prepare a presentation state quickly. Real votes submitted through `/api/elections/{election_id}/vote` still require valid ZKP proofs.
