# Deployment

This project supports local Poetry development and Docker-based execution. Docker is recommended for generating ZKP artifacts because it avoids installing Rust and Circom directly on the host machine.

## Local Development

Install dependencies:

```powershell
poetry install
npm ci
```

Create `.env`:

```powershell
Copy-Item .env.example .env
```

Run the app:

```powershell
poetry run uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/
```

API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## ZKP Artifact Setup With Docker

Generate artifacts:

```powershell
docker compose --profile tools run --rm zkp-setup
```

This creates files in `zkp_artifacts/`, including:

- `powersOfTau28_hez_final_14.ptau`
- `vote_eligibility.r1cs`
- `vote_eligibility_final.zkey`
- `verification_key.json`
- `vote_eligibility_js/vote_eligibility.wasm`
- `vote_eligibility_js/generate_witness.js`

The setup uses a public prepared Powers of Tau file and verifies its BLAKE2b hash before using it. Full transcript verification is optional because it is slower:

```powershell
$env:VERIFY_PTAU_TRANSCRIPT="1"
docker compose --profile tools run --rm zkp-setup
```

## Application With Docker

Build and run:

```powershell
docker compose build app
docker compose up app
```

The app container mounts:

- `./data:/app/data`
- `./output:/app/output`
- `./zkp_artifacts:/app/zkp_artifacts:ro`

The SQLite database remains on the host in `data/`. Demo output files remain on the host in `output/`.

The app image also contains `scripts/` and `circuits/`, so demo helpers can be run inside Docker:

```powershell
docker compose run --rm app python scripts/seed_demo.py --reset
docker compose run --rm app python scripts/extract_token.py --input output/demo/demo_active_available_tokens.json --index 0 --output output/demo/demo_active_token_1.json
docker compose run --rm app python scripts/voter_client.py --package output/demo/demo_active_token_1.json --candidate-id 1 --output output/demo/vote_payload.json
```

## Demo Data

Create demo records:

```powershell
poetry run python scripts/seed_demo.py
```

Reset demo records:

```powershell
poetry run python scripts/seed_demo.py --reset
```

Clear demo records:

```powershell
poetry run python scripts/seed_demo.py --clear
```

Demo records are identified by the `[DEMO]` election-name prefix. The clear/reset commands do not delete non-demo elections.

When using Docker, the same commands can be run through the app service:

```powershell
docker compose run --rm app python scripts/seed_demo.py --reset
```

## Network Access

For access from another device on the same local network, bind Uvicorn to all interfaces:

```powershell
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then open:

```text
http://<local-ip-address>:8000/docs
```

Windows Firewall may need to allow inbound traffic on port `8000`.

## Temporary Public Tunnel

The tunnel is not part of the FastAPI codebase. Run it as a separate process after the app is already listening on port `8000`.

Terminal 1:

```powershell
poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```powershell
ngrok http 8000
```

Use the HTTPS URL printed by ngrok, for example:

```text
https://example-id.ngrok-free.app/
```

That public URL forwards requests to your local app, including:

- `/` for the browser UI,
- `/admin/login` for administrator login,
- `/docs` for API documentation,
- `/vendor/snarkjs.min.js` and `/zkp-artifacts/*` for browser-side proof generation.

Keep the tunnel running only during a demo. Anyone with the public URL can reach the local application, so use demo credentials and demo data.

Alternative with Cloudflare Tunnel:

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

Use whichever tool is easier to install on the presentation machine. The project itself does not need code changes for either tunnel.

## Production Notes

This repository is an educational simulator, not a production voting system. Before production use, the project would require:

- HTTPS-only cookies.
- Secure admin password storage instead of plain `.env` comparison.
- A production database instead of local SQLite.
- Stronger operational controls for token distribution.
- Larger Merkle tree depth and optimized tree construction.
- Security review of the ZKP circuit and setup process.
- Additional hardening of browser-side proof generation and voter package handling.
