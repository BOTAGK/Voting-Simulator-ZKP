# ZKP Voting Simulator

ZKP Voting Simulator is an educational election management and vote-counting project built with FastAPI, SQLite, Circom, Poseidon hashing, Merkle trees, and snarkjs. It demonstrates how a voter can prove eligibility without sending the private voter token to the backend, while the backend still prevents double voting with an election-scoped nullifier hash.

## Features

- Administrator login with signed cookie sessions.
- Election lifecycle management: `draft`, `active`, `closed`.
- Active-election access respects `starts_at` and `ends_at`.
- Candidate CRUD for draft elections.
- Candidate CSV import.
- Voter token generation with Poseidon hashes and Merkle proofs.
- One-time voter token packages exported as JSON or CSV.
- Browser frontend for voter package loading, local ZKP proof generation, voting, admin management, and results.
- Public voting endpoint protected by Groth16 proof verification.
- Duplicate-vote prevention with `nullifier_hash`.
- Public results for closed elections.
- Admin results for all elections.
- Results CSV export for public and admin views.
- Demo seed script with draft, active, and closed elections.
- Docker-based ZKP setup for reproducible Circom/snarkjs artifacts.
- Unit and integration tests for API, services, ZKP helpers, CSV, seed data, and scripts.

## Scope & Limitations

- This is an educational simulator, not a production election system.
- SQLite is used for local development and demos. A production deployment would need a server database, migrations, backups, monitoring, and stronger operational controls.
- The demo Circom circuit uses Merkle tree depth `10`, which means up to `1024` token leaves. This keeps proof generation fast for presentations. A real national-scale setup would require a larger and more optimized tree strategy.
- The browser frontend is intended for local/demo use. The JSON API remains available through `/docs` for inspection and manual testing.
- Demo seed votes use real election records and real nullifier hashes, but stored demo `proof_json` values are placeholders. Votes submitted through the public vote endpoint are verified through the ZKP verification path.
- Administrator credentials are read from environment variables. This is enough for the project scope, but not a production-grade identity system.

## Architecture

The backend uses layered FastAPI architecture. Routes expose HTTP endpoints, services enforce business rules, repositories perform SQLAlchemy database access, and ZKP helpers integrate Poseidon, Merkle trees, Circom artifacts, and snarkjs.

```text
Browser UI / API docs / scripts
          |
          v
FastAPI routes: app/api/routes/*
          |
          v
Services: app/services/*
          |
          +--> Repositories: app/repositories/* --> SQLite database
          |
          +--> ZKP helpers: app/zkp/* + circuits/* + zkp_artifacts/*
```

Main modules:

- `app/api/routes/` - public, admin, auth, result, and health endpoints.
- `app/services/` - election, candidate, token, voting, tally, and ZKP business logic.
- `app/repositories/` - SQLAlchemy persistence functions.
- `app/models/` - SQLAlchemy ORM models.
- `app/schemas/` - Pydantic request and response models.
- `app/zkp/` - Poseidon bridge, Merkle tree, artifact paths, and snarkjs client.
- `circuits/` - Circom vote eligibility circuit.
- `app/web/` - Jinja templates and JavaScript modules for voter/admin browser flows.
- `scripts/` - demo seed, voter client, ZKP setup, and helper scripts.
- `docs/` - architecture, database, deployment, and ZKP notes.

The browser frontend loads voter packages in `sessionStorage`, generates proofs locally with snarkjs, and sends only proof data and public signals to the backend.

## Requirements

Runtime requirements are derived from `pyproject.toml`, `package.json`, `Dockerfile`, and `Dockerfile.zkp`.

- Python `>=3.14`
- Poetry `>=2.0`
- Node.js and npm
- Python dependencies installed with `poetry install`. Exact versions are declared in `pyproject.toml` and locked in `poetry.lock`.
- npm dependencies installed with `npm ci`. Exact versions are declared in `package.json` and locked in `package-lock.json`.
- For local non-Docker ZKP setup:
  - Circom compiler
  - snarkjs
  - Bash/PowerShell depending on the selected script
- Recommended for ZKP setup:
  - Docker and Docker Compose

## Installation

Clone the repository:

```powershell
git clone https://github.com/BOTAGK/Voting-Simulator-ZKP.git
cd Voting-Simulator-ZKP
```

Install Python dependencies:

```powershell
poetry install
```

Install Node dependencies:

```powershell
npm ci
```

Create local environment configuration:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set admin credentials and a strong session secret:

```env
APP_NAME=ZKP Voting Simulator
DATABASE_URL=sqlite:///./data/zkp_voting.db
ZKP_ARTIFACTS_DIR=./zkp_artifacts
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-this-password
SESSION_SECRET_KEY=change-this-secret-key
```

Generate ZKP artifacts with Docker:

```powershell
docker compose --profile tools run --rm zkp-setup
```

There are no Alembic migrations in this version. Tables are created automatically by `init_db()` during application startup.

## Configuration

| Variable | Description | Default/example |
| --- | --- | --- |
| `APP_NAME` | Human-readable application name. | `ZKP Voting Simulator` |
| `DATABASE_URL` | SQLAlchemy database URL. SQLite is used by default. | `sqlite:///./data/zkp_voting.db` |
| `ZKP_ARTIFACTS_DIR` | Directory containing generated proving and verification artifacts. | `./zkp_artifacts` |
| `ADMIN_USERNAME` | Administrator username used by `/api/auth/login`. | `your-admin-username` |
| `ADMIN_PASSWORD` | Administrator password used by `/api/auth/login`. | `your-admin-password` |
| `SESSION_SECRET_KEY` | Secret key used to sign admin session cookies. | `your-session-secret-key` |

## Usage

Run the API locally:

```powershell
poetry run uvicorn app.main:app --reload
```

Open API docs:

```text
http://127.0.0.1:8000/docs
```

Open the browser UI:

```text
http://127.0.0.1:8000/
```

Run with Docker:

```powershell
docker compose up app
```

Run demo scripts inside the app container:

```powershell
docker compose run --rm app python scripts/seed_demo.py --reset
docker compose run --rm app python scripts/extract_token.py --input output/demo/demo_active_available_tokens.json --index 0 --output output/demo/demo_active_token_1.json
```

Seed demo data:

```powershell
poetry run python scripts/seed_demo.py
```

Reset demo data:

```powershell
poetry run python scripts/seed_demo.py --reset
```

Clear only demo data:

```powershell
poetry run python scripts/seed_demo.py --clear
```

Demo token packages are written to:

```text
output/demo/
```

Generate a vote payload from a voter package with the CLI helper:

```powershell
poetry run python scripts/extract_token.py --input output/demo/demo_active_available_tokens.json --index 0 --output output/demo/demo_active_token_1.json
poetry run python scripts/voter_client.py --package output/demo/demo_active_token_1.json --candidate-id 1 --output output/demo/vote_payload.json
```

The first command extracts one unused demo token package. The second command builds a vote payload from that token package.

For the browser flow, open `/voter`, load a token package JSON file, go to the active election, select a candidate, and submit the vote. The proof is generated locally in the browser.

Token packages are generated only once per election. In the admin browser UI, click `Generate JSON` first; the `Download CSV` button exports the same generated packages from browser memory without calling token generation again. Save the downloaded files because private `token_secret` values are not stored in the database.

Candidate CSV import accepts `name` and optional `description` columns. A ready-to-edit example is available in `docs/examples/candidates.csv`.

Expose the local app to other devices on the same network:

```powershell
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then open:

```text
http://<your-local-ip>:8000/docs
```

Expose the local app through a temporary public tunnel with ngrok:

```powershell
ngrok http 8000
```

Use the HTTPS URL printed by ngrok. Tunnel instructions belong in `docs/deployment.md`; no FastAPI code change is required.

## API Reference

All API paths are mounted under `/api`.

Authentication:

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/auth/login` | Login administrator with `username` and `password`. |
| `POST` | `/api/auth/logout` | Logout administrator. Requires admin session. |
| `GET` | `/api/auth/me` | Return current administrator. Requires admin session. |

Health:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Return `{"status": "ok"}`. |

Public voting:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/elections/active` | List active elections within their configured date window. |
| `GET` | `/api/elections/{election_id}` | Read active election details if it is within its configured date window. |
| `GET` | `/api/elections/{election_id}/candidates` | List candidates for an active election within its configured date window. |
| `POST` | `/api/elections/{election_id}/vote` | Submit a vote with proof, public signals, candidate id, and nullifier hash. |

Public results:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/elections/{election_id}/results` | Read results for a closed election. |
| `GET` | `/api/elections/{election_id}/results/csv` | Export results CSV for a closed election. |

Admin elections:

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/admin/elections` | Create election. |
| `GET` | `/api/admin/elections` | List all elections. |
| `GET` | `/api/admin/elections/{election_id}` | Read any election. |
| `PATCH` | `/api/admin/elections/{election_id}` | Update draft election. |
| `DELETE` | `/api/admin/elections/{election_id}` | Delete any election and its related rows. |
| `POST` | `/api/admin/elections/{election_id}/open` | Open draft election. |
| `POST` | `/api/admin/elections/{election_id}/cancel` | Cancel draft election by marking it as closed. |
| `POST` | `/api/admin/elections/{election_id}/close` | Close active election. |

Admin candidates:

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/admin/elections/{election_id}/candidates` | Add candidate to draft election. |
| `GET` | `/api/admin/elections/{election_id}/candidates` | List candidates. |
| `POST` | `/api/admin/elections/{election_id}/candidates/import` | Import candidates from CSV. |
| `GET` | `/api/admin/elections/{election_id}/candidates/{candidate_id}` | Read candidate. |
| `PATCH` | `/api/admin/elections/{election_id}/candidates/{candidate_id}` | Update candidate in draft election. |
| `DELETE` | `/api/admin/elections/{election_id}/candidates/{candidate_id}` | Delete candidate from draft election. |

Admin tokens and results:

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/admin/elections/{election_id}/tokens/generate` | Generate one-time voter token packages as JSON for a draft election. |
| `POST` | `/api/admin/elections/{election_id}/tokens/generate/csv` | Generate one-time voter token packages as CSV for a draft election. |
| `GET` | `/api/admin/elections/{election_id}/tokens` | List stored public token metadata without token secrets. |
| `GET` | `/api/admin/elections/{election_id}/results` | Read results for any election. |
| `GET` | `/api/admin/elections/{election_id}/results/csv` | Export results CSV for any election. |

Example administrator login:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/auth/login" `
  -H "Content-Type: application/json" `
  -d "{\"username\":\"admin\",\"password\":\"change-this-password\"}" `
  -c cookies.txt
```

Example create election:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/admin/elections" `
  -H "Content-Type: application/json" `
  -b cookies.txt `
  -d "{\"name\":\"Demo election\",\"description\":\"Created from curl\"}"
```

## Running Tests

Run the full test suite:

```powershell
poetry run pytest -q
```

Run selected tests:

```powershell
poetry run pytest -q tests/unit/test_merkle.py
poetry run pytest -q tests/integration/test_zkp_e2e.py
```

The project currently uses pytest without a configured coverage tool.

## Contributing

Suggested branch naming:

- `feature/<short-description>`
- `fix/<short-description>`
- `docs/<short-description>`
- `test/<short-description>`

Suggested commit message format:

- `feat: add public election endpoints`
- `fix: reject duplicate nullifier hashes`
- `test: cover voter token CSV export`
- `docs: document ZKP setup flow`

Pull request checklist:

- Run `poetry run pytest -q`.
- Keep generated secrets, `.env`, SQLite files, and token packages out of commits.
- Update README or `docs/` when changing setup, API behavior, or ZKP flow.
- Keep business validation in services, not only in routes or frontend.

## License

MIT License. See `LICENSE`.
