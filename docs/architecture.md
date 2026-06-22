# Architecture

This project is a layered FastAPI application with a small ZKP toolchain around Circom and snarkjs.

## Layers

```text
Browser UI / HTTP clients
    |
    v
app/web routes + app/api/routes
    |
    v
app/services
    |
    +--> app/repositories --> SQLAlchemy models --> SQLite
    |
    +--> app/zkp --> Circom/snarkjs artifacts
```

## Route Layer

Routes live in `app/api/routes/`.

- `auth.py` handles administrator login, logout, and current-session lookup.
- `admin.py` exposes election, candidate, token, and admin-result operations.
- `voting.py` exposes public active-election and vote-submission operations.
- `results.py` exposes public closed-election results.
- `health.py` exposes a healthcheck endpoint.

Routes should remain thin. They should parse HTTP inputs, call services, and return response models.

## Service Layer

Services live in `app/services/`.

- `election_service.py` owns election lifecycle rules.
- `candidate_service.py` owns candidate validation and CSV import.
- `token_service.py` generates voter secrets, token hashes, Merkle proofs, and token packages.
- `voting_service.py` validates active elections, election date windows, candidates, nullifiers, and ZKP proofs before storing votes.
- `tally_service.py` calculates vote counts, turnout, and result responses.
- `zkp_service.py` validates public signals and delegates proof verification to snarkjs.

Business rules belong in services so they apply consistently to API routes, web views, scripts, and tests.

## Repository Layer

Repositories live in `app/repositories/` and contain SQLAlchemy queries. They do not enforce business policy.

## Data Layer

Models live in `app/models/models.py`.

Main tables:

- `elections`
- `candidates`
- `voter_tokens`
- `votes`

SQLite is the default database. The schema is created automatically at application startup by `app.core.database.init_db()`.

## ZKP Layer

ZKP modules live in `app/zkp/`.

- `poseidon.py` calls `scripts/poseidon_cli.mjs` and `circomlibjs`.
- `merkle.py` builds a fixed-depth Merkle tree for token hashes.
- `snarkjs_client.py` generates and verifies Groth16 proofs.
- `paths.py` resolves artifact paths from `ZKP_ARTIFACTS_DIR`.
- `proof_models.py` defines public signals and circuit input models.

The circuit lives in `circuits/vote_eligibility.circom`.

## Frontend Layer

The `app/web/` directory contains the browser UI.

- Jinja templates render the voter, election, result, login, and admin pages.
- JavaScript modules in `app/web/static/js/` keep client logic separated by responsibility:
  - `app.js` starts the frontend modules,
  - `admin.js` handles the administrator dashboard,
  - `admin-api.js` wraps admin fetch calls,
  - `csv.js` builds browser-side CSV exports,
  - `voter-package.js` loads and clears voter token packages,
  - `vote.js` generates browser-side ZKP proofs and submits votes,
  - `shared.js` contains small reusable UI/API helpers.

When an administrator is logged in, the top navigation intentionally shows only the admin view. Voter-facing pages remain available to non-admin users.
