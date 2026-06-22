# Demo Scenario

This scenario prepares a predictable local state for a project presentation.

## 1. Prepare Environment

Install dependencies:

```powershell
poetry install
npm ci
```

Create `.env`:

```powershell
Copy-Item .env.example .env
```

Edit administrator credentials in `.env`.

## 2. Generate ZKP Artifacts

Use Docker:

```powershell
docker compose --profile tools run --rm zkp-setup
```

This creates files in `zkp_artifacts/`. These files are required by proof generation and backend verification.

## 3. Create Demo Data

Run:

```powershell
poetry run python scripts/seed_demo.py --reset
```

The seed creates:

- `[DEMO] Draft election` with status `draft`,
- `[DEMO] Active voting` with status `active`,
- `[DEMO] Closed election` with status `closed`.

It also writes voter token packages into:

```text
output/demo/
```

Useful files:

- `demo_active_tokens.json` - all generated active-election token packages.
- `demo_active_available_tokens.json` - active-election token packages that were not used by demo votes.
- `demo_closed_tokens.json` - token packages generated for historical closed results.

## 4. Run Application

```powershell
poetry run uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/
```

API documentation remains available at:

```text
http://127.0.0.1:8000/docs
```

## 5. Administrator Flow

1. Open `/admin/login` and log in with credentials from `.env`.
2. The admin navigation shows only the administrator dashboard.
3. Select an election from the admin table.
4. For draft elections, you can edit details, add/import candidates, generate voter tokens, open the election, cancel it to `closed`, or delete it.
5. Generate token packages once with `Generate JSON`. Use `Download CSV` immediately after that if you want the same package set as CSV.
6. View active or closed results with the `Results` button.
7. Export results with `Export results CSV`.

Token packages are generated only once per election. The private `token_secret` values are not stored in the database, so the downloaded JSON/CSV files must be saved if they are needed later.

## 6. Voter Flow

Extract one available active token package:

```powershell
poetry run python scripts/extract_token.py --input output/demo/demo_active_available_tokens.json --index 0 --output output/demo/demo_active_token_1.json
```

Option A: browser voting flow:

1. Open `/voter`.
2. Load `output/demo/demo_active_token_1.json`.
3. Follow the link to the active election.
4. Select a candidate and submit the vote.

The proof is generated locally in the browser. The backend receives only the proof, public signals, selected candidate, and nullifier hash.

Option B: CLI helper flow:

```powershell
poetry run python scripts/voter_client.py --package output/demo/demo_active_token_1.json --candidate-id 1 --output output/demo/vote_payload.json
```

Submit the payload to:

```text
POST /api/elections/{election_id}/vote
```

Submitting another vote with the same token should fail because the same `nullifier_hash` already exists for that election.

## 7. Public Results Flow

Closed results are available without admin login:

```text
GET /api/elections/{election_id}/results
GET /api/elections/{election_id}/results/csv
```

Active election results are not public. They are available only through admin endpoints.

## 8. Network Demo

For another device on the same network:

```powershell
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

For a temporary public URL:

```powershell
ngrok http 8000
```

Use the HTTPS URL printed by ngrok.
