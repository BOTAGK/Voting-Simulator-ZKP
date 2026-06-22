# Database Schema

The application uses SQLAlchemy ORM models and SQLite by default. Tables are created automatically by `app.core.database.init_db()`.

## Tables

### `elections`

Stores election metadata and lifecycle state.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer | Primary key. |
| `name` | string(120) | Required, indexed. |
| `description` | text | Optional. |
| `status` | enum | `draft`, `active`, or `closed`. |
| `merkle_root` | string(255) | Root of the generated voter-token Merkle tree. |
| `starts_at` | datetime | Optional. |
| `ends_at` | datetime | Optional. |
| `created_at` | datetime | Database timestamp. |

Relationships:

- one election has many candidates,
- one election has many voter tokens,
- one election has many votes.

### `candidates`

Stores candidates assigned to elections.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer | Primary key. |
| `election_id` | integer | Foreign key to `elections.id`, indexed. |
| `name` | string(120) | Required, indexed. |
| `description` | text | Optional. |

### `voter_tokens`

Stores public metadata for generated voter tokens. Private `token_secret` values are not stored.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer | Primary key. |
| `election_id` | integer | Foreign key to `elections.id`, indexed. |
| `token_hash` | string(255) | Poseidon hash of the private token secret. |
| `merkle_index` | integer | Leaf index in the Merkle tree. |
| `merkle_path_json` | text | Serialized Merkle proof for the token. |
| `label_for_admin` | string(120) | Optional export/admin label. |
| `created_at` | datetime | Database timestamp. |

Constraints:

- unique `(election_id, token_hash)`.

### `votes`

Stores accepted votes.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer | Primary key. |
| `election_id` | integer | Foreign key to `elections.id`, indexed. |
| `candidate_id` | integer | Foreign key to `candidates.id`, indexed. |
| `nullifier_hash` | string(255) | Election-scoped double-vote prevention value. |
| `proof_json` | text | Serialized Groth16 proof. |
| `public_signals_json` | text | Serialized public signals used for verification. |
| `created_at` | datetime | Database timestamp. |

Constraints:

- unique `(election_id, nullifier_hash)`.

## Cascades

The ORM relationships use `cascade="all, delete-orphan"` from `Election` to candidates, voter tokens, and votes. Deleting an election through the ORM deletes related rows.

## Migrations

Alembic is not used in the current version. The schema is initialized from SQLAlchemy models on app startup. For a larger deployment, adding Alembic migrations would be the next step.
