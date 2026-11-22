from base64 import b64decode
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from httpx2 import MockTransport, Request, Response

from ecommerce_store_ba.api.app import create_app
from ecommerce_store_ba.application.knowledge import EvidenceBundle
from tests.smoke_create_mobile_phone import NAME_RULE, SCENARIO_TITLE, SmokeFailure, check_evidence, finish, prepare
from tests.test_sessions import (
    ALLURE_URL,
    HEADERS,
    SNAPSHOT_ID,
    MemoryRepository,
    MemoryRuns,
    ProcessFixture,
    knowledge_response,
    knowledge_settings,
    resolve_evidence,
)

PNG = b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a5x0AAAAASUVORK5CYII=")
BOARD = "https://www.figma.com/board/BA123/CreateMobilePhone?node-id=1-2"


@pytest.fixture
def ba_client() -> Iterator[tuple[TestClient, list[tuple[str, str]]]]:
    calls: list[tuple[str, str]] = []

    def upstream(request: Request) -> Response:
        calls.append((request.method, request.url.path))
        return knowledge_response(request)

    app = create_app(
        knowledge_settings(),
        MemoryRepository(),
        run_repository=MemoryRuns(),
        knowledge_transport=MockTransport(upstream),
        agent=ProcessFixture(),
    )
    with TestClient(app, headers=HEADERS) as client:
        yield client, calls


def test_smoke_checks_contract_validation_and_bdd_then_claims_figjam(
    ba_client: tuple[TestClient, list[tuple[str, str]]],
) -> None:
    client, calls = ba_client
    run, figjam = prepare(client)
    assert run.draft is not None and run.draft.snapshot_id == SNAPSHOT_ID
    assert run.status == "figjam_pending"
    assert figjam.mermaid_syntax == run.draft.mermaid
    assert calls == [("GET", "/api/v1/catalog"), ("POST", "/api/v1/query"), ("POST", "/api/v1/query")]


def test_smoke_rejects_missing_bdd_evidence(ba_client: tuple[TestClient, list[tuple[str, str]]]) -> None:
    client, _ = ba_client
    _, _, response = resolve_evidence(client)
    evidence = EvidenceBundle.model_validate(response.json()["response"])
    incomplete = evidence.model_copy(update={"scenarios": [], "missing_evidence": ["scenario"]})
    with pytest.raises(SmokeFailure, match="passed CreateMobilePhone BDD scenario"):
        check_evidence(incomplete, SNAPSHOT_ID)


def test_smoke_saves_the_figjam_png_and_evidence_description(
    ba_client: tuple[TestClient, list[tuple[str, str]]],
    tmp_path: Path,
) -> None:
    client, calls = ba_client
    run, _ = prepare(client)
    output = finish(client, run.session_id, run.id, BOARD, PNG, tmp_path)
    assert output == tmp_path / str(run.id)
    assert {file.name for file in output.iterdir()} == {"diagram.png", "description.txt"}
    assert (output / "diagram.png").read_bytes() == PNG
    description = (output / "description.txt").read_text(encoding="utf-8")
    for expected in (
        "POST /mobile-phones",
        "commonDescription",
        NAME_RULE,
        SCENARIO_TITLE,
        "Given I have valid mobile phone details",
        "When I submit the create mobile phone request",
        "Then the mobile phone is created successfully",
        SNAPSHOT_ID,
        ALLURE_URL,
        BOARD,
    ):
        assert expected in description
    assert finish(client, run.session_id, run.id, BOARD, PNG, tmp_path) == output
    assert len(calls) == 3


def test_smoke_rejects_invalid_png_before_saving_artifacts(
    ba_client: tuple[TestClient, list[tuple[str, str]]],
    tmp_path: Path,
) -> None:
    client, _ = ba_client
    run, _ = prepare(client)
    with pytest.raises(SmokeFailure, match="PNG screenshot"):
        finish(client, run.session_id, run.id, BOARD, b"invalid image", tmp_path)
    assert list(tmp_path.iterdir()) == []
