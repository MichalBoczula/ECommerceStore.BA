from argparse import ArgumentParser
from dataclasses import dataclass
from json import dumps
from os import getenv
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit
from uuid import UUID, uuid4

from httpx2 import Client, RequestError
from pydantic import BaseModel, ValidationError

from ecommerce_store_ba.api.contracts import ExchangeResponse, SessionResponse
from ecommerce_store_ba.api.runs import FigJamArguments, FigJamClaim, PublicationRequest, RunResponse
from ecommerce_store_ba.application.knowledge import ContractSection, EvidenceBundle
from ecommerce_store_ba.application.run_models import Draft
from ecommerce_store_ba.domain.session import ExchangeSource

SESSIONS = "/api/v1/sessions"
OPERATION = {"service": "products", "method": "POST", "path": "/mobile-phones"}
SCENARIO_TITLE = "Creating a phone stores an active catalogue entry and its first history snapshot"
NAME_RULE = "Name cannot be null or whitespace."
RESULTS = Path(__file__).resolve().parents[1] / "tests-results" / "create-mobile-phone"


class SmokeFailure(Exception):
    pass


class AllureStep(BaseModel):
    name: str
    status: str


class AllureExecution(BaseModel):
    name: str
    status: str
    steps: list[AllureStep]


@dataclass(frozen=True, slots=True)
class ObservedEvidence:
    bundle: EvidenceBundle
    contract: ContractSection
    scenario: AllureExecution
    allure_url: str


def check_evidence(bundle: EvidenceBundle, snapshot_id: str) -> ObservedEvidence:
    sources = {source.id: source for source in bundle.sources}
    if (
        bundle.service != "products"
        or bundle.snapshot_id != snapshot_id
        or len(sources) != len(bundle.sources)
        or any((source.service, source.snapshot_id) != (bundle.service, snapshot_id) for source in sources.values())
    ):
        raise SmokeFailure("Expected Products evidence and citations from one pinned snapshot.")

    contract = bundle.contract
    if (
        contract is None
        or (contract.operation_id, contract.method, contract.path) != ("CreateMobilePhone", "POST", "/mobile-phones")
        or contract.request_schema.get("type") != "object"
        or not isinstance(required := contract.request_schema.get("required"), list)
        or "commonDescription" not in required
        or not contract.source_ids
        or not sources.keys() >= set(contract.source_ids)
    ):
        raise SmokeFailure("Expected the cited CreateMobilePhone request contract.")

    if not any(
        rule.description == NAME_RULE and rule.source_ids and sources.keys() >= set(rule.source_ids)
        for rule in bundle.validation_rules
    ):
        raise SmokeFailure("Expected the cited validation rule for the mobile phone name.")

    for scenario in bundle.scenarios:
        if scenario.title != SCENARIO_TITLE or scenario.execution_status != "passed":
            continue
        execution = AllureExecution.model_validate_json(scenario.content)
        keywords = {step.name.split(maxsplit=1)[0] for step in execution.steps if step.name.strip()}
        if (
            execution.name != SCENARIO_TITLE
            or execution.status != "passed"
            or not {"Given", "When", "Then"} <= keywords
        ):
            continue
        if any(step.status != "passed" for step in execution.steps):
            continue
        for source_id in scenario.source_ids:
            source = sources.get(source_id)
            if source is None or source.url is None or not source.path.startswith("allure-results/"):
                continue
            link = urlsplit(source.url)
            if link.scheme == "https" and link.path.endswith("/products/allure/") and link.fragment == "behaviors":
                return ObservedEvidence(bundle, contract, execution, source.url)
    raise SmokeFailure("Expected the passed CreateMobilePhone BDD scenario with executed steps and an Allure link.")


def prepare(client: Client) -> tuple[RunResponse, FigJamArguments]:
    session = _request(client, "POST", SESSIONS, SessionResponse, {"operation": "model-flow"})
    run_id = uuid4()
    path = _run_path(session.id, run_id)
    run = _request(client, "PUT", path, RunResponse, OPERATION)
    draft, _ = _run_evidence(client, run, session.id, run_id)
    claim = _request(client, "POST", f"{path}/figjam", FigJamClaim, {"draftSha256": draft.checksum})
    if (
        not claim.claimed
        or claim.arguments is None
        or claim.run.id != run.id
        or claim.run.session_id != session.id
        or claim.run.draft_sha256 != draft.checksum
        or claim.arguments.mermaid_syntax != draft.mermaid
        or not draft.mermaid.strip()
    ):
        raise SmokeFailure("Expected one FigJam claim for the saved BA draft.")
    return claim.run, claim.arguments


def finish(
    client: Client, session_id: UUID, run_id: UUID, figjam_url: str, png: bytes, results: Path = RESULTS
) -> Path:
    run = _request(client, "GET", _run_path(session_id, run_id), RunResponse)
    draft, evidence = _run_evidence(client, run, session_id, run_id)
    if run.figjam_requested_at is None:
        raise SmokeFailure("Prepare and claim the FigJam diagram for this run first.")
    link = PublicationRequest.model_validate({"draftSha256": draft.checksum, "figjamUrl": figjam_url}).figjam_url
    if (
        len(png) < 45
        or not png.startswith(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
        or not all(int.from_bytes(png[offset : offset + 4], "big") for offset in (16, 20))
        or not png.endswith(b"\x00\x00\x00\x00IEND\xaeB`\x82")
    ):
        raise SmokeFailure("Expected a PNG screenshot of the FigJam diagram.")

    description = "\n".join(
        [
            "CreateMobilePhone smoke test",
            f"Operation: {evidence.contract.method} {evidence.contract.path}",
            f"Snapshot: {evidence.bundle.snapshot_id}",
            f"Run: {run.id}",
            f"Draft SHA-256: {draft.checksum}",
            "",
            "Request schema",
            dumps(
                {
                    "schema": evidence.contract.request_schema,
                    "referenceSchemas": evidence.contract.reference_schemas,
                },
                indent=2,
                ensure_ascii=False,
            ),
            "",
            "Validation",
            *(f"- {rule.description}" for rule in evidence.bundle.validation_rules),
            "",
            f"Observed BDD scenario ({evidence.scenario.status})",
            evidence.scenario.name,
            *(step.name for step in evidence.scenario.steps),
            "",
            "Evidence sources",
            *(
                f"- {source.path} ({source.url})" if source.url else f"- {source.path}"
                for source in evidence.bundle.sources
            ),
            f"Allure: {evidence.allure_url}",
            f"FigJam: {link}",
            "",
        ]
    ).encode("utf-8")

    results.mkdir(parents=True, exist_ok=True)
    output = results / str(run.id)
    with TemporaryDirectory(dir=results) as temporary:
        staging = Path(temporary)
        (staging / "diagram.png").write_bytes(png)
        (staging / "description.txt").write_bytes(description)
        try:
            staging.rename(output)
        except OSError:
            if not output.is_dir():
                raise
            if (output / "diagram.png").read_bytes() != png or (output / "description.txt").read_bytes() != description:
                raise SmokeFailure(f"Different artifacts already exist for run {run.id}.") from None
    return output


def _run_path(session_id: UUID, run_id: UUID) -> str:
    return f"{SESSIONS}/{session_id}/runs/{run_id}"


def _run_evidence(client: Client, run: RunResponse, session_id: UUID, run_id: UUID) -> tuple[Draft, ObservedEvidence]:
    draft = run.draft
    if draft is None or (run.session_id, run.id) != (session_id, run_id):
        raise SmokeFailure("Expected the saved draft for this BA session and run.")
    exchange = _request(
        client, "GET", f"{SESSIONS}/{session_id}/exchanges/{draft.evidence_exchange_id}", ExchangeResponse
    )
    if (exchange.session_id, exchange.id, exchange.source) != (
        session_id,
        draft.evidence_exchange_id,
        ExchangeSource.RAG,
    ):
        raise SmokeFailure("Expected the captured RAG exchange for this BA draft.")
    bundle = EvidenceBundle.model_validate(exchange.response)
    if bundle.sources != draft.sources:
        raise SmokeFailure("Expected the draft to cite its captured RAG evidence.")
    return draft, check_evidence(bundle, draft.snapshot_id)


def _request[T: BaseModel](
    client: Client, method: str, path: str, model: type[T], body: dict[str, str] | None = None
) -> T:
    response = client.request(method, path, json=body)
    if not response.is_success:
        raise SmokeFailure(f"BA {method} {path} returned HTTP {response.status_code}.")
    return model.model_validate_json(response.content, extra="ignore")


def main() -> None:
    parser = ArgumentParser(
        description="Check CreateMobilePhone evidence and save the FigJam screenshot and description."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("prepare", help="Prepare the BA run and return the FigJam tool arguments.")
    save = commands.add_parser("finish", help="Save the PNG downloaded from FigJam and the evidence description.")
    save.add_argument("session_id", type=UUID)
    save.add_argument("run_id", type=UUID)
    save.add_argument("figjam_url")
    save.add_argument("png_path", type=Path)
    args = parser.parse_args()
    key = getenv("BA_API_KEY")
    if not key:
        parser.error("Set BA_API_KEY in the environment.")
    with Client(
        base_url=getenv("BA_BASE_URL", "http://localhost:8082"), headers={"X-Api-Key": key}, timeout=195
    ) as client:
        try:
            if args.command == "prepare":
                run, figjam = prepare(client)
                print(
                    dumps(
                        {
                            "sessionId": str(run.session_id),
                            "runId": str(run.id),
                            "draftSha256": run.draft_sha256,
                            "arguments": figjam.model_dump(by_alias=True),
                        },
                        indent=2,
                    )
                )
            else:
                print(finish(client, args.session_id, args.run_id, args.figjam_url, args.png_path.read_bytes()))
        except (SmokeFailure, OSError) as error:
            parser.exit(1, f"{error}\n")
        except RequestError:
            parser.exit(1, "The BA request did not complete. Check BA_BASE_URL and the local BA service.\n")
        except ValidationError:
            parser.exit(1, "Expected valid BA evidence and a link to an editable FigJam board.\n")


if __name__ == "__main__":
    main()
