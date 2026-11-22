from dataclasses import replace
from datetime import datetime
from json import loads
from os import getenv
from uuid import UUID, uuid4
from xml.etree.ElementTree import fromstring

import pytest
from fastapi.testclient import TestClient
from httpx2 import MockTransport, Request, Response
from pydantic import AnyHttpUrl, JsonValue, SecretStr
from pymongo import MongoClient

from ecommerce_store_ba.api.app import create_app
from ecommerce_store_ba.application.knowledge import EvidenceBundle
from ecommerce_store_ba.application.run_errors import JiraUnavailableError, RunBusyError
from ecommerce_store_ba.application.run_models import AgentReceipt, JiraContext, JiraReference, Run
from ecommerce_store_ba.domain.process import AcceptanceCriterion, Actor, ProcessDraft, Step, Transition
from ecommerce_store_ba.domain.session import Exchange, Session
from ecommerce_store_ba.infrastructure.settings import Settings


class MemoryRepository:
    def __init__(self) -> None:
        self.sessions: dict[UUID, Session] = {}
        self.exchanges: dict[tuple[UUID, UUID], Exchange] = {}

    async def add_session(self, session: Session) -> None:
        self.sessions[session.id] = session

    async def get_session(self, session_id: UUID) -> Session | None:
        return self.sessions.get(session_id)

    async def pin_snapshot(self, session_id: UUID, snapshot_id: str) -> None:
        session = self.sessions.get(session_id)
        if session is not None and session.snapshot_id is None:
            self.sessions[session_id] = replace(session, snapshot_id=snapshot_id)

    async def get_exchange(self, session_id: UUID, exchange_id: UUID) -> Exchange | None:
        return self.exchanges.get((session_id, exchange_id))

    async def store_exchange(self, exchange: Exchange) -> Exchange:
        return self.exchanges.setdefault((exchange.session_id, exchange.id), exchange)


def _exercise_session(client: TestClient) -> tuple[str, str, dict[str, str]]:
    headers = {"X-Api-Key": "test-only-key"}
    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").status_code == 200
    assert client.post("/api/v1/sessions", json={"operation": "model-flow"}).status_code == 401
    invalid = client.post("/api/v1/sessions", json={"operation": "invalid"}, headers=headers)
    assert invalid.status_code == 400
    assert invalid.headers["content-type"] == "application/problem+json"
    assert invalid.json()["traceId"] == invalid.headers["x-trace-id"]
    created = client.post(
        "/api/v1/sessions",
        json={"operation": "model-flow", "jiraIssueKey": "STORE-12", "snapshotId": "snapshot-1"},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    session_url = f"/api/v1/sessions/{created.json()['id']}"
    assert client.get(session_url, headers=headers).json() == created.json()
    exchange_url = f"{session_url}/exchanges/{uuid4()}"
    assert client.get(exchange_url, headers=headers).status_code == 404
    capture = {
        "source": "agent",
        "request": {"$key.with.dots": "test prompt", "context": ["doc-1"]},
        "response": {"answer": "test answer"},
        "model": "synthetic-test-model",
    }
    recorded = client.put(exchange_url, json=capture, headers=headers)
    assert recorded.status_code == 200, recorded.text
    assert recorded.json()["request"] == capture["request"]
    assert recorded.json()["response"] == capture["response"]
    assert client.put(exchange_url, json=capture, headers=headers).json() == recorded.json()
    changed = client.put(exchange_url, json={**capture, "response": {"answer": "changed"}}, headers=headers)
    assert changed.status_code == 409
    assert client.get(exchange_url, headers=headers).json() == recorded.json()
    oversized = client.put(
        f"{session_url}/exchanges/{uuid4()}",
        json={**capture, "response": "x" * (256 * 1024)},
        headers=headers,
    )
    assert oversized.status_code == 413
    unknown_session_url = f"/api/v1/sessions/{uuid4()}/exchanges/{uuid4()}"
    assert client.put(unknown_session_url, json=capture, headers=headers).status_code == 404
    return session_url, exchange_url, headers


def test_session_and_immutable_capture() -> None:
    app = create_app(Settings(api_key=SecretStr("test-only-key")), MemoryRepository())
    with TestClient(app) as client:
        _exercise_session(client)
        schema = client.get("/openapi.json").json()
        operation = schema["paths"]["/api/v1/sessions"]["post"]
        assert "422" not in operation["responses"]
        assert operation["responses"]["400"]["content"]["application/problem+json"]["schema"] == {
            "$ref": "#/components/schemas/ProblemDetails"
        }
        assert operation["security"]


SNAPSHOT_ID = "v1-test"
REQUEST = {"service": "products", "method": "POST", "path": "/mobile-phones"}
HEADERS = {"X-Api-Key": "test-only-key"}
ALLURE_URL = "https://docs.example.test/livedoc/v1/products/allure/#behaviors"


def _knowledge_settings(**changes: object) -> Settings:
    return Settings.model_validate(
        {
            "api_key": SecretStr("test-only-key"),
            "knowledge_api_url": AnyHttpUrl("https://knowledge.example.test"),
            "knowledge_api_key": SecretStr("upstream-test-key"),
            **changes,
        }
    )


def _source(source_id: str, url: str) -> dict[str, JsonValue]:
    return {
        "id": source_id,
        "title": source_id,
        "snapshotId": SNAPSHOT_ID,
        "service": "products",
        "commitSha": "a" * 40,
        "bundleSha256": "b" * 64,
        "path": f"products/{source_id}.json",
        "url": url,
    }


def _knowledge_response(request: Request) -> Response:
    assert request.headers["X-Api-Key"] == "upstream-test-key"
    if request.url.path == "/api/v1/catalog":
        assert request.method == "GET"
        return Response(
            200,
            json={
                "snapshots": [
                    {"id": "demo-v1", "isDemo": True, "services": ["products"]},
                    {"id": SNAPSHOT_ID, "isDemo": False, "services": ["products"]},
                ]
            },
        )
    assert (request.method, request.url.path) == ("POST", "/api/v1/query")
    query = loads(request.content)
    assert query["service"] == "products"
    assert query["snapshotId"] == SNAPSHOT_ID
    contract: dict[str, JsonValue] = {
        "type": "api_contract",
        "title": "Create a mobile phone",
        "method": "POST",
        "path": "/mobile-phones",
        "operationId": "CreateMobilePhone",
        "mediaType": "application/json",
        "requestSchema": {"required": ["name"], "type": "object"},
        "referenceSchemas": {},
        "exampleRequest": {"name": "Example Phone"},
        "exampleOrigin": "openapi",
        "exampleSchemaValid": True,
        "sourceIds": ["contract"],
    }
    sources = [_source("contract", "https://docs.example.test/livedoc/v1/products/openapi.json")]
    if query["question"] == "POST /mobile-phones contract and validation":
        section: dict[str, JsonValue] = {
            "type": "validation",
            "title": "Validation",
            "sourceIds": ["policy"],
            "rules": [{"field": "name", "description": "Name is required.", "sourceIds": ["policy"]}],
        }
        sources.append(_source("policy", "https://docs.example.test/livedoc/v1/products/validation.json"))
        request_id = "contract-request"
    else:
        assert query["question"] == "POST /mobile-phones"
        section = {
            "type": "scenario",
            "title": "Creating a phone stores an active catalogue entry and its first history snapshot",
            "content": "The customer sees the new active phone.",
            "executionStatus": "passed",
            "sourceIds": ["scenario"],
        }
        sources.append(_source("scenario", ALLURE_URL))
        request_id = "scenario-request"
    return Response(
        200,
        json={
            "requestId": request_id,
            "snapshotId": SNAPSHOT_ID,
            "service": "products",
            "isDemo": False,
            "sections": [contract, section],
            "sources": sources,
            "limitations": [],
        },
    )


def _resolve_evidence(client: TestClient) -> tuple[str, UUID, Response]:
    session = client.post("/api/v1/sessions", json={"operation": "model-flow"}, headers=HEADERS)
    assert session.status_code == 201
    session_url = f"/api/v1/sessions/{session.json()['id']}"
    exchange_id = uuid4()
    resolved = client.put(f"{session_url}/evidence/{exchange_id}", json=REQUEST, headers=HEADERS)
    return session_url, exchange_id, resolved


def test_resolve_evidence_pins_snapshot_and_replays_the_capture() -> None:
    calls: list[str] = []

    def upstream(request: Request) -> Response:
        calls.append(request.url.path)
        return _knowledge_response(request)

    app = create_app(_knowledge_settings(), MemoryRepository(), knowledge_transport=MockTransport(upstream))
    with TestClient(app) as client:
        session_url, exchange_id, resolved = _resolve_evidence(client)
        assert resolved.status_code == 200, resolved.text
        result = resolved.json()
        evidence = result["response"]
        assert result["source"] == "rag"
        assert evidence["snapshotId"] == SNAPSHOT_ID
        assert evidence["contract"]["operationId"] == "CreateMobilePhone"
        assert evidence["validationRules"][0]["field"] == "name"
        assert evidence["scenarios"][0]["executionStatus"] == "passed"
        assert any(source["url"] == ALLURE_URL for source in evidence["sources"])
        assert evidence["missingEvidence"] == []
        assert client.get(session_url, headers=HEADERS).json()["snapshotId"] == SNAPSHOT_ID
        assert client.get(f"{session_url}/exchanges/{exchange_id}", headers=HEADERS).json() == result
        url = f"{session_url}/evidence/{exchange_id}"
        assert client.put(url, json=REQUEST, headers=HEADERS).json() == result
        assert client.put(url, json={**REQUEST, "method": "GET"}, headers=HEADERS).status_code == 409
        assert calls == ["/api/v1/catalog", "/api/v1/query", "/api/v1/query"]


@pytest.mark.parametrize("failure", ["different_scope", "unknown_source", "unrelated_operation"])
def test_evidence_with_a_mismatched_contract_or_provenance(failure: str) -> None:
    def upstream(request: Request) -> Response:
        original = _knowledge_response(request)
        if request.method == "GET":
            return original
        answer = original.json()
        if failure == "different_scope":
            answer["snapshotId"] = "another-snapshot"
        elif failure == "unknown_source":
            answer["sections"][0]["sourceIds"] = ["unknown"]
        else:
            answer["sections"][0]["path"] = "/another-operation"
        return Response(200, json=answer)

    app = create_app(_knowledge_settings(), MemoryRepository(), knowledge_transport=MockTransport(upstream))
    with TestClient(app) as client:
        session_url, exchange_id, resolved = _resolve_evidence(client)
        exchange = client.get(f"{session_url}/exchanges/{exchange_id}", headers=HEADERS)
        if failure == "unrelated_operation":
            assert resolved.status_code == 200, resolved.text
            evidence = resolved.json()["response"]
            assert evidence["missingEvidence"] == ["api_contract", "scenario", "validation"]
            assert evidence["sources"] == []
            assert exchange.json() == resolved.json()
        else:
            assert resolved.status_code == 502, resolved.text
            assert resolved.json()["code"] == "knowledge_invalid_response"
            assert exchange.status_code == 404


def test_inactive_pinned_snapshot_is_not_replaced() -> None:
    app = create_app(_knowledge_settings(), MemoryRepository(), knowledge_transport=MockTransport(_knowledge_response))
    with TestClient(app) as client:
        session = client.post(
            "/api/v1/sessions", json={"operation": "model-flow", "snapshotId": "old-snapshot"}, headers=HEADERS
        )
        url = f"/api/v1/sessions/{session.json()['id']}"
        failure = client.put(f"{url}/evidence/{uuid4()}", json=REQUEST, headers=HEADERS)
        assert failure.status_code == 409
        assert failure.json()["code"] == "knowledge_snapshot_unavailable"
        assert client.get(url, headers=HEADERS).json()["snapshotId"] == "old-snapshot"


class MemoryRuns:
    def __init__(self) -> None:
        self.runs: dict[tuple[UUID, UUID], Run] = {}
        self.leases: dict[tuple[UUID, UUID], UUID] = {}

    async def put(self, run: Run) -> Run:
        return self.runs.setdefault((run.session_id, run.id), run)

    async def get(self, session_id: UUID, run_id: UUID) -> Run | None:
        return self.runs.get((session_id, run_id))

    async def claim(self, session_id: UUID, run_id: UUID, token: UUID, now: datetime, until: datetime) -> Run | None:
        key = session_id, run_id
        if key in self.leases:
            return None
        self.leases[key] = token
        return self.runs[key]

    async def save(self, run: Run, token: UUID) -> None:
        key = run.session_id, run.id
        if self.leases.get(key) != token:
            raise RunBusyError
        self.runs[key] = run

    async def release(self, session_id: UUID, run_id: UUID, token: UUID) -> None:
        if self.leases.get((session_id, run_id)) == token:
            del self.leases[session_id, run_id]


class ProcessFixture:
    def __init__(self, *, source_id: str = "contract") -> None:
        self.calls = 0
        self.source_id = source_id

    async def draft(self, evidence: EvidenceBundle, jira: JiraContext | None) -> tuple[ProcessDraft, AgentReceipt]:
        self.calls += 1
        assert evidence.snapshot_id == SNAPSHOT_ID
        source_ids = [self.source_id]
        process = ProcessDraft(
            title="Create mobile phone",
            actors=[Actor(id="catalog", name="Products Catalog")],
            steps=[
                Step(id="start", actor_id="catalog", kind="start", label="Receive request", source_ids=source_ids),
                Step(id="check", actor_id="catalog", kind="decision", label="Valid request?", source_ids=["policy"]),
                Step(id="saved", actor_id="catalog", kind="end", label="Phone created", source_ids=["scenario"]),
                Step(id="reject", actor_id="catalog", kind="end", label="Reject request", source_ids=["policy"]),
            ],
            transitions=[
                Transition(from_id="start", to_id="check", kind="main", condition="", source_ids=source_ids),
                Transition(from_id="check", to_id="saved", kind="main", condition="Valid", source_ids=["scenario"]),
                Transition(
                    from_id="check", to_id="reject", kind="exception", condition="Invalid", source_ids=["policy"]
                ),
            ],
            acceptance_criteria=[
                AcceptanceCriterion(
                    title="A valid phone is registered",
                    given="Valid input",
                    when="The phone is submitted",
                    then="It is created",
                    source_ids=["scenario"],
                )
            ],
            open_questions=[],
        )
        return process, AgentReceipt(name="ba", version="1", response_id="resp-1", model="gpt-6-luna")


class JiraCreateThenLoseResponse:
    def __init__(self) -> None:
        self.creates = 0
        self.issue: JiraReference | None = None

    async def context(self, key: str) -> JiraContext:
        raise AssertionError("Expected publication to a new issue")

    async def find_created_issue(self, run: Run) -> JiraReference | None:
        return self.issue

    async def create_issue(self, run: Run) -> JiraReference:
        self.creates += 1
        assert run.figjam_url == "https://www.figma.com/board/BA123/Create-mobile-phone"
        self.issue = JiraReference(key="STORE-100", url="https://jira.example.test/browse/STORE-100")
        raise JiraUnavailableError

    async def update_issue(self, key: str, run: Run) -> JiraReference:
        raise AssertionError("Expected publication to a new issue")


def _exercise_run(client: TestClient) -> str:
    session_url, evidence_id, evidence = _resolve_evidence(client)
    assert evidence.status_code == 200, evidence.text
    run_url = f"{session_url}/runs/{uuid4()}"
    request = {**REQUEST, "evidenceExchangeId": str(evidence_id)}
    prepared = client.put(run_url, json=request, headers=HEADERS)
    assert prepared.status_code == 200, prepared.text
    draft = prepared.json()
    assert draft["draft"]["evidenceExchangeId"] == str(evidence_id)
    assert draft["draft"]["process"]["steps"][1]["sourceIds"] == ["policy"]
    assert client.put(run_url, json=request, headers=HEADERS).json() == draft
    assert client.get(f"{run_url}/handoff", headers=HEADERS).status_code == 409
    bpmn = client.get(f"{run_url}/artifacts/process.bpmn", headers=HEADERS)
    assert bpmn.status_code == 200
    xml = fromstring(bpmn.content)
    assert len(xml.findall(".//{*}exclusiveGateway")) == 1
    assert len(xml.findall(".//{*}BPMNEdge")) == 3
    approval = {"draftSha256": draft["draftSha256"]}
    claim = client.post(f"{run_url}/figjam", json=approval, headers=HEADERS)
    assert claim.json()["claimed"] is True
    assert '-.->|"Invalid"|' in claim.json()["arguments"]["mermaidSyntax"]
    assert client.post(f"{run_url}/figjam", json=approval, headers=HEADERS).json()["claimed"] is False
    publication = {**approval, "figjamUrl": "https://www.figma.com/board/BA123/Create-mobile-phone"}
    assert (
        client.put(f"{run_url}/publication", json={**publication, "draftSha256": "0" * 64}, headers=HEADERS).status_code
        == 409
    )
    assert client.put(f"{run_url}/publication", json=publication, headers=HEADERS).status_code == 503
    assert client.get(run_url, headers=HEADERS).json()["status"] == "jira_pending"
    result = client.put(f"{run_url}/publication", json=publication, headers=HEADERS)
    assert result.status_code == 200, result.text
    assert result.json()["jiraIssue"]["key"] == "STORE-100"
    assert client.put(f"{run_url}/publication", json=publication, headers=HEADERS).json() == result.json()
    assert client.get(f"{run_url}/handoff", headers=HEADERS).json() == result.json()
    return run_url


def test_run_reuses_evidence_and_recovers_jira_without_a_second_create() -> None:
    agent = ProcessFixture()
    jira = JiraCreateThenLoseResponse()
    app = create_app(
        _knowledge_settings(),
        MemoryRepository(),
        knowledge_transport=MockTransport(_knowledge_response),
        run_repository=MemoryRuns(),
        agent=agent,
        jira=jira,
    )
    with TestClient(app) as client:
        _exercise_run(client)
    assert agent.calls == jira.creates == 1


def test_run_rejects_agent_citations_outside_the_evidence() -> None:
    app = create_app(
        _knowledge_settings(),
        MemoryRepository(),
        knowledge_transport=MockTransport(_knowledge_response),
        run_repository=MemoryRuns(),
        agent=ProcessFixture(source_id="made-up-source"),
    )
    with TestClient(app) as client:
        session = client.post("/api/v1/sessions", json={"operation": "model-flow"}, headers=HEADERS)
        url = f"/api/v1/sessions/{session.json()['id']}/runs/{uuid4()}"
        response = client.put(url, json=REQUEST, headers=HEADERS)
        assert response.status_code == 502, response.text
        assert response.json()["code"] == "agent_invalid_response"
        assert client.get(url, headers=HEADERS).json()["draft"] is None


@pytest.mark.skipif(not getenv("TEST_MONGODB_URI"), reason="Set TEST_MONGODB_URI to run real MongoDB checks")
def test_mongodb_persists_capture_across_restarts() -> None:
    uri = getenv("TEST_MONGODB_URI", "")
    database = f"test_ba_{uuid4().hex}"
    settings = _knowledge_settings(mongodb_uri=SecretStr(uri), mongodb_database=database)
    try:
        with TestClient(
            create_app(
                settings,
                knowledge_transport=MockTransport(_knowledge_response),
                agent=ProcessFixture(),
                jira=JiraCreateThenLoseResponse(),
            )
        ) as client:
            session_url, exchange_url, headers = _exercise_session(client)
            captured = client.get(exchange_url, headers=headers).json()
            evidence_session, evidence_id, evidence = _resolve_evidence(client)
            assert evidence.status_code == 200, evidence.text
            evidence_json = evidence.json()
            run_url = _exercise_run(client)
            run_json = client.get(f"{run_url}/handoff", headers=HEADERS).json()
        with TestClient(create_app(settings)) as client:
            assert client.get(session_url, headers=headers).json()["jiraIssueKey"] == "STORE-12"
            assert client.get(exchange_url, headers=headers).json() == captured
            assert client.get(evidence_session, headers=headers).json()["snapshotId"] == SNAPSHOT_ID
            replay = client.put(f"{evidence_session}/evidence/{evidence_id}", json=REQUEST, headers=HEADERS)
            assert replay.json() == evidence_json
            assert client.get(f"{run_url}/handoff", headers=HEADERS).json() == run_json
    finally:
        with MongoClient[dict[str, object]](uri, timeoutMS=3000) as mongo:
            mongo.drop_database(database)
