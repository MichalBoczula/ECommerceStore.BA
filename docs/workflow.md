# Prepare and publish a BA run

Start with `products`, `POST /mobile-phones`. A BA run resolves the operation against the session's LiveDocs snapshot. It saves the sourced process, acceptance criteria, unanswered questions, and export files in MongoDB under a caller-generated UUID.

## Configuration

| Provider | Settings |
| --- | --- |
| BA API and MongoDB | `BA_API_KEY`, `BA_MONGODB_URI`, optionally `BA_MONGODB_DATABASE` |
| Knowledge Assistant | `BA_KNOWLEDGE_API_URL`, `BA_KNOWLEDGE_API_KEY` |
| Azure Foundry | `BA_FOUNDRY_PROJECT_ENDPOINT`, `BA_FOUNDRY_AGENT_NAME`, `BA_FOUNDRY_AGENT_VERSION`, optionally `BA_FOUNDRY_MAX_OUTPUT_TOKENS` |
| Jira Cloud | `BA_JIRA_SITE_URL`, `BA_JIRA_EMAIL`, `BA_JIRA_API_TOKEN`, `BA_JIRA_PROJECT_KEY`, `BA_JIRA_ISSUE_TYPE_ID`, optionally `BA_JIRA_API_URL` |
| CLI | `BA_BASE_URL` defaults to `http://localhost:8082`. It uses `BA_API_KEY` as its caller credential. |
| FigJam | Sign in to Figma MCP in a supported client such as Codex. The client calls `generate_diagram`. |

Use the Foundry project URL ending in `/api/projects/<project>`. With your Azure CLI login, run `uv run --locked python scripts/create_foundry_agent.py` to create a version of `ecommerce-business-analyst` on the `gpt-6-luna` deployment. The script prints the agent name and version to configure. Set the version before starting BA. A deployed BA app uses its managed identity with **Azure AI User** on the Foundry project. For a local Foundry call, run BA with `uv` on the machine with your Azure CLI login and a reachable MongoDB URI.

Set `BA_JIRA_SITE_URL` to the Jira site root for issue links. For a scoped Jira token, set `BA_JIRA_API_URL` to `https://api.atlassian.com/ex/jira/<cloud-id>`. Select the target project and a create-screen issue type that accepts Summary, Description and Labels. The Jira identity needs Browse Projects, Create Issues and, for an existing issue, Edit Issues in that project.

## Endpoints

All run routes use the existing BA `X-Api-Key`. Paths below are relative to `/api/v1/sessions/{sessionId}/runs/{runId}`.

| Method and path | Input and result |
| --- | --- |
| `PUT` run root | Send `service`, `method`, `path`, and optionally `evidenceExchangeId`. With an evidence ID, BA reads that earlier capture. Otherwise it resolves and persists the operation evidence. |
| `GET` run root | Read the draft, `draftSha256`, snapshot, source records, agent version and publication state. |
| `GET /artifacts/{name}` | Download `flow.json`, `process.bpmn` or `process.mmd`. The BPMN file includes lanes, conditions and diagram coordinates. |
| `POST /figjam` | Approve the draft by its `draftSha256` and claim one diagram generation. Use the returned `arguments` with Figma MCP when `claimed` is true. |
| `PUT /publication` | Send the approved `draftSha256` and the resulting `figjamUrl` pointing to the editable board. The call saves that link and creates or updates the Jira issue. |
| `GET /handoff` | Read the published flow for QA with the evidence exchange ID, pinned snapshot, citations, approval, Jira issue and FigJam board. |

Create a `model-flow` session first. An optional `jiraIssueKey` tells BA to read that Jira issue's requirements for the draft and publish into the same issue. BA adds its versioned section to the description. With no issue key, publication creates an issue in the configured project. An approved existing FigJam board link can be submitted directly to publication.

## Use the run CLI

```sh
uv run --locked python scripts/ba_run.py session
uv run --locked python scripts/ba_run.py prepare SESSION_ID RUN_ID products POST /mobile-phones
uv run --locked python scripts/ba_run.py review SESSION_ID RUN_ID
```

Use the returned session ID and a UUID you generate for the run. Review `draft.process`, the `sourceIds`, and `openQuestions` before publishing. Ask Codex to publish that run through Figma MCP using the repository instructions, or use `scripts/ba_run.py figjam` and `publish` to complete the same steps from another supported client.

## Local smoke test

Run the basic Python regressions with `uv run --locked pytest -q tests/test_smoke_create_mobile_phone.py`. The fixtures exercise BA's two Knowledge queries, the captured Allure evidence, and the PNG and TXT output.

For a live smoke, run BA with a reachable Knowledge Assistant and the configured Foundry agent. Set the client environment variables `BA_BASE_URL` and `BA_API_KEY`. In an authenticated Codex session with Figma MCP, invoke `$smoke-ba-create-mobile-phone` to run the test. The test checks `POST /mobile-phones`, the cited name validation rule, and the passed Allure scenario with Given/When/Then steps in one snapshot. The RAG Allure evaluation maps this scenario to `REF07_CreateMobilePhone_01`. [Allure evaluation suite](https://github.com/MichalBoczula/ECommerceStore.KnowledgeAssistant.Api/blob/main/evaluation/allure-v1.json)

The smoke has two local commands for the steps around Figma MCP.

```sh
uv run --locked python -m tests.smoke_create_mobile_phone prepare
uv run --locked python -m tests.smoke_create_mobile_phone finish SESSION_ID RUN_ID FIGJAM_URL PNG_PATH
```

Use the first command's FigJam arguments with `generate_diagram` and capture the resulting diagram with `get_screenshot`. Pass the downloaded PNG and the board link to the second command. It saves `diagram.png` and `description.txt` under `tests-results/create-mobile-phone/<runId>/`. Each run has its own output directory. [Figma MCP tools](https://developers.figma.com/docs/figma-mcp-server/tools-and-prompts/)

## Resume publication

Reuse the session ID, run ID, draft hash and FigJam URL for every retry. BA keeps the generated draft and checkpoints publication in MongoDB. While `figjam_pending`, use the existing board link from the completed MCP call or locate the board by the BA run suffix. With `jira_pending`, a repeated publication looks up the issue by its run label. If Jira definitively rejects create, the same publication can attempt create after the configuration is corrected. An existing Jira issue is updated with one section per run.

## Package for DEV

On pushes to `main`, CI publishes the tested and scanned BA image to Docker Hub with the commit SHA and `latest` tags. A manual run on `main` publishes the commit SHA tag. Publication uses `DOCKER_USER` and `DOCKER_TOKEN`. Use `imageReference` from the `image-reference` artifact to set `app_images.ba` in Terraform. The deployment review and provider acceptance are tracked in BA/06.
