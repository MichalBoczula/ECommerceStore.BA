from typing import cast
from uuid import uuid5

from httpx2 import AsyncClient, ConnectError, ConnectTimeout, PoolTimeout, RequestError, Response
from pydantic import BaseModel, Field, JsonValue, ValidationError

from ecommerce_store_ba.application.run_errors import JiraRejectedError, JiraUnavailableError
from ecommerce_store_ba.application.run_models import JiraContext, JiraReference, Run

type Node = dict[str, JsonValue]


class _IssueKey(BaseModel):
    key: str = Field(pattern=r"^[A-Z][A-Z0-9_]*-[0-9]+$")


class _IssueFields(BaseModel):
    summary: str
    description: Node | None = None
    updated: str


class _Issue(_IssueKey):
    fields: _IssueFields


class _Search(BaseModel):
    issues: list[_IssueKey]


class JiraClient:
    def __init__(self, client: AsyncClient, site_url: str, project: str, issue_type_id: str) -> None:
        self._client = client
        self._site_url = site_url.rstrip("/")
        self._project = project
        self._issue_type_id = issue_type_id

    async def context(self, key: str) -> JiraContext:
        self._check_project(key)
        response = await self._request("GET", f"issue/{key}", params={"fields": "summary,description,updated"})
        issue = _parse(response, _Issue)
        self._check_project(issue.key)
        return JiraContext(
            key=issue.key,
            url=self._browse(issue.key),
            summary=issue.fields.summary,
            description=issue.fields.description,
            updated=issue.fields.updated,
        )

    async def create_issue(self, run: Run) -> JiraReference:
        assert run.draft is not None
        response = await self._request(
            "POST",
            "issue",
            json={
                "fields": {
                    "project": {"key": self._project},
                    "issuetype": {"id": self._issue_type_id},
                    "summary": run.draft.process.title[:255],
                    "labels": [_marker(run)],
                    "description": _doc([_panel(run)]),
                }
            },
        )
        return self._reference(_parse(response, _IssueKey).key)

    async def find_created_issue(self, run: Run) -> JiraReference | None:
        marker = _marker(run)
        response = await self._request(
            "POST",
            "search/jql",
            json={"jql": f'project = "{self._project}" AND labels = "{marker}"', "fields": ["key"], "maxResults": 2},
        )
        issues = _parse(response, _Search).issues
        if len(issues) > 1:
            raise JiraUnavailableError
        return self._reference(issues[0].key) if issues else None

    async def update_issue(self, key: str, run: Run) -> JiraReference:
        issue = await self.context(key)
        marker_block = _paragraph(f"BA process {_marker(run)}")
        description = issue.description or _doc([])
        original = description.get("content")
        if description.get("type") != "doc" or description.get("version") != 1 or not isinstance(original, list):
            raise JiraUnavailableError
        panel = _panel(run)
        managed = [block for block in original if _matches_panel(block, marker_block)]
        if managed != [panel]:
            content = [block for block in original if not _matches_panel(block, marker_block)]
            await self._request(
                "PUT",
                f"issue/{issue.key}",
                json={"fields": {"description": {**description, "content": [*content, panel]}}},
            )
        return self._reference(issue.key)

    def _check_project(self, key: str) -> None:
        if not key.startswith(f"{self._project}-"):
            raise JiraRejectedError

    def _browse(self, key: str) -> str:
        return f"{self._site_url}/browse/{key}"

    def _reference(self, key: str) -> JiraReference:
        if not key.startswith(f"{self._project}-"):
            raise JiraUnavailableError
        return JiraReference(key=key, url=self._browse(key))

    async def _request(
        self, method: str, path: str, *, json: Node | None = None, params: dict[str, str] | None = None
    ) -> Response:
        try:
            response = await self._client.request(method, path, json=json, params=params)
        except ConnectError, ConnectTimeout, PoolTimeout:
            raise JiraRejectedError from None
        except RequestError:
            raise JiraUnavailableError from None
        if response.status_code in {400, 401, 403, 404, 422, 429}:
            raise JiraRejectedError
        if not response.is_success:
            raise JiraUnavailableError
        return response


def _parse[T: BaseModel](response: Response, schema: type[T]) -> T:
    try:
        return schema.model_validate_json(response.content)
    except ValidationError:
        raise JiraUnavailableError from None


def _marker(run: Run) -> str:
    return f"ba-run-{uuid5(run.session_id, str(run.id)).hex}"


def _doc(blocks: list[Node]) -> Node:
    return {"type": "doc", "version": 1, "content": cast(list[JsonValue], blocks)}


def _paragraph(value: str, url: str | None = None) -> Node:
    text: Node = {"type": "text", "text": value}
    if url is not None and url.startswith("https://"):
        text["marks"] = [{"type": "link", "attrs": {"href": url}}]
    return {"type": "paragraph", "content": [text]}


def _matches_panel(node: JsonValue, marker: Node) -> bool:
    if not isinstance(node, dict) or node.get("type") != "panel":
        return False
    content = node.get("content")
    return isinstance(content, list) and bool(content) and content[0] == marker


def _panel(run: Run) -> Node:
    assert run.draft is not None and run.figjam_url is not None
    draft = run.draft
    process = draft.process
    actors = {actor.id: actor.name for actor in process.actors}
    steps = {step.id: step.label for step in process.steps}
    content: list[Node] = [
        _paragraph(f"BA process {_marker(run)}"),
        _paragraph(process.title),
        _paragraph(f"{run.request.method} {run.request.path} · LiveDocs {draft.snapshot_id} · Draft {draft.checksum}"),
        _paragraph("Editable process in FigJam", run.figjam_url),
        _paragraph("Steps"),
    ]
    content.extend(
        _paragraph(f"{actors[step.actor_id]} · {step.label} [{', '.join(step.source_ids)}]") for step in process.steps
    )
    content.append(_paragraph("Transitions"))
    for transition in process.transitions:
        condition = f" if {transition.condition}" if transition.condition else ""
        content.append(
            _paragraph(
                f"{transition.kind.title()} · {steps[transition.from_id]} → {steps[transition.to_id]}"
                f"{condition} [{', '.join(transition.source_ids)}]"
            )
        )
    if process.acceptance_criteria:
        content.append(_paragraph("Acceptance criteria"))
    for criterion in process.acceptance_criteria:
        content.append(
            _paragraph(
                f"{criterion.title} — Given {criterion.given}. When {criterion.when}. Then {criterion.then}. "
                f"[{', '.join(criterion.source_ids)}]"
            )
        )
    content.append(_paragraph("Sources"))
    for source in draft.sources:
        content.append(_paragraph(f"[{source.id}] {source.title} · {source.path} · {source.commit_sha}", source.url))
    if draft.jira_context is not None:
        issue = draft.jira_context
        content.append(_paragraph(f"[{issue.source_id}] {issue.summary} · {issue.updated}", issue.url))
    questions = [
        *process.open_questions,
        *draft.limitations,
        *(f"Missing evidence for {kind}" for kind in draft.missing_evidence),
    ]
    if questions:
        content.append(_paragraph("Open questions and evidence gaps"))
        content.extend(_paragraph(question) for question in questions if question.strip())
    return {"type": "panel", "attrs": {"panelType": "info"}, "content": cast(list[JsonValue], content)}
