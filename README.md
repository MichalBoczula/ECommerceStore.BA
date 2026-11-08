# ECommerceStore.BA

Foundation for modeling business processes from Jira requirements and Knowledge Assistant evidence.

## Run locally

```sh
BA_API_KEY=local-dev-key docker compose up --build
```

Swagger is at `http://localhost:8082/swagger`. Session routes require `X-Api-Key`.
Compose creates a MongoDB volume. To run the API against an existing MongoDB,
set `BA_API_KEY`, `BA_MONGODB_URI`, and optionally `BA_MONGODB_DATABASE`
before running `uv run --locked uvicorn ecommerce_store_ba.main:app --port 8082`.

| Endpoint | Purpose |
| --- | --- |
| `GET /health/live` | Process probe |
| `GET /health/ready` | MongoDB connectivity probe |
| `POST /api/v1/sessions` | Register a session and optionally pin `jiraIssueKey` and `snapshotId` |
| `GET /api/v1/sessions/{id}` | Read session metadata |
| `PUT /api/v1/sessions/{id}/exchanges/{exchangeId}` | Record an immutable request/response pair |
| `GET /api/v1/sessions/{id}/exchanges/{exchangeId}` | Read the recorded pair |

Create a session with `{"operation":"model-flow","jiraIssueKey":"STORE-12","snapshotId":"snapshot-1"}`.
Capture JSON with `source` (`agent`, `jira`, or `rag`), `request`, `response`
and optional `model`. Use a distinct UUID per exchange and reuse it when retrying
the same write. A different payload for the same session and exchange IDs returns
`409`. The combined canonical JSON limit is 256 KiB. Clients supply reviewed,
redacted payloads before capture. Request headers are outside the evidence contract.

## Verification

Use Python from `.python-version` and uv from `pyproject.toml`.
Run `bash scripts/ci.sh` for locked install, format, lint, typing, API tests
and the wheel build. Set `TEST_MONGODB_URI` to run the database-backed restart test.
CI supplies a MongoDB service and builds the Docker image.

See [low-level design](docs/lld.md).

## BA documentation lab

Use the [CreateMobilePhone Copilot lab](docs/labs/create-mobile-phone/README.md)
to compare a plain prompt with the repository skill on the same pinned Products
Catalog evidence.
