# ECommerceStore.BA

Model sourced business processes from Knowledge Assistant evidence and Jira requirements. Review a versioned draft, publish its diagram to FigJam and its criteria to Jira, then hand off the approved flow to QA.

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
| `PUT /api/v1/sessions/{id}/evidence/{exchangeId}` | Resolve and record Knowledge Assistant evidence for an operation |

Create a session with `{"operation":"model-flow","jiraIssueKey":"STORE-12","snapshotId":"snapshot-1"}`.
Capture JSON with `source` (`agent`, `jira`, or `rag`), `request`, `response`
and optional `model`. Use a distinct UUID per exchange and reuse it when retrying
the same write. A different payload for the same session and exchange IDs returns
`409`. The combined canonical JSON limit is 256 KiB. Clients supply reviewed,
redacted payloads before capture. Request headers are outside the evidence contract.

## Resolve operation evidence

Set `BA_KNOWLEDGE_API_URL` to the Knowledge API base URL and
`BA_KNOWLEDGE_API_KEY` to its server-side key. Compose passes both environment
variables through when set. Create a `model-flow` session and send the operation
to the evidence route with a caller-generated exchange UUID.

```json
{"service": "products", "method": "POST", "path": "/mobile-phones"}
```

BA checks the active Knowledge catalog before querying it. A session with a supplied
`snapshotId` uses that snapshot. For an unpinned session, BA pins the sole live
snapshot for the service. An unavailable or ambiguous snapshot returns
`409 knowledge_snapshot_unavailable`.

The response uses the existing exchange format with `source: rag`. Its
`response` contains the contract, scenarios, validation rules, source IDs and
links, Knowledge request IDs, and any upstream limitations. `missingEvidence`
lists evidence categories absent for the requested operation. Source records
include the snapshot, source commit and bundle digest. Repeat the PUT with the
same UUID to read the captured result. The exchange can also be read through
the exchanges route.

## Verification

Use Python from `.python-version` and uv from `pyproject.toml`.
Run `bash scripts/ci.sh` for locked install, format, lint, typing, API tests
and the wheel build. Set `TEST_MONGODB_URI` to run the database-backed restart test.
CI supplies a MongoDB service and builds the Docker image.

See [low-level design](docs/lld.md).

## BA workflow

See [ADR 0001 · Evidence-backed BA workflow](docs/adr/0001-evidence-backed-ba-workflow.md) for component responsibilities, the run lifecycle, and retry behavior.

Use the [BA run guide](docs/workflow.md) for Foundry configuration, the review and publication API, FigJam, and QA handoff.

Run the [local CreateMobilePhone smoke test](docs/workflow.md#local-smoke-test) to check RAG evidence and save a FigJam PNG and description.

## BA documentation lab

Use the [CreateMobilePhone Copilot lab](docs/labs/create-mobile-phone/README.md)
to compare a plain prompt with the repository skill on the same pinned Products
Catalog evidence.
