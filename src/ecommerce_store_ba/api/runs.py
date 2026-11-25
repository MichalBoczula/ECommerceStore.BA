from collections.abc import Awaitable, Callable
from re import fullmatch
from typing import Annotated, Literal, cast
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Request, Response
from pydantic import AnyHttpUrl, Field, computed_field, field_validator

from ecommerce_store_ba.api.contracts import ApiModel
from ecommerce_store_ba.api.errors import UNAVAILABLE, RequestProblem, problem_responses
from ecommerce_store_ba.application.run_errors import RunNotReadyError
from ecommerce_store_ba.application.run_models import Run, RunRequest
from ecommerce_store_ba.application.run_service import RunService


class DraftApproval(ApiModel):
    draft_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class PublicationRequest(DraftApproval):
    figjam_url: AnyHttpUrl

    @field_validator("figjam_url")
    @classmethod
    def board_link(cls, url: AnyHttpUrl) -> AnyHttpUrl:
        if (
            url.scheme != "https"
            or url.host not in {"figma.com", "www.figma.com"}
            or url.username is not None
            or url.password is not None
            or url.port != 443
            or not fullmatch(r"/board/[A-Za-z0-9]+(?:/[^/]*)?/?", url.path or "")
        ):
            raise ValueError("Supply the HTTPS link to an editable FigJam board.")
        return url


class RunResponse(Run):
    @computed_field
    @property
    def draft_sha256(self) -> str | None:
        return self.draft.checksum if self.draft is not None else None

    @computed_field
    @property
    def status(self) -> str:
        if self.published_at is not None:
            return "published"
        if self.jira_requested_at is not None:
            return "jira_pending"
        if self.figjam_url is not None:
            return "ready_for_jira"
        if self.figjam_requested_at is not None:
            return "figjam_pending"
        return "draft" if self.draft is not None else "preparing"

    @classmethod
    def from_run(cls, run: Run) -> RunResponse:
        return cls.model_validate(run.model_dump())


class FigJamArguments(ApiModel):
    name: str
    mermaid_syntax: str


class FigJamClaim(ApiModel):
    claimed: bool
    run: RunResponse
    arguments: FigJamArguments | None


def _service(request: Request) -> RunService:
    service = cast(RunService | None, request.app.state.run_service)
    if service is None:
        raise RequestProblem(UNAVAILABLE)
    return service


def run_router(authorize: Callable[..., Awaitable[None]]) -> APIRouter:
    router = APIRouter(prefix="/api/v1/sessions/{session_id}/runs", tags=["BA runs"], dependencies=[Depends(authorize)])

    @router.put(
        "/{run_id}",
        summary="Prepare a sourced BA draft",
        responses=problem_responses(400, 401, 404, 409, 413, 502, 503, 504),
    )
    async def prepare(
        session_id: UUID,
        run_id: UUID,
        body: Annotated[
            RunRequest,
            Body(
                openapi_examples={
                    "create-phone": {
                        "summary": "Draft the Create Mobile Phone flow",
                        "value": {"service": "products", "method": "POST", "path": "/mobile-phones"},
                    }
                }
            ),
        ],
        service: Annotated[RunService, Depends(_service)],
    ) -> RunResponse:
        """Use a caller-generated `run_id` UUID. BA resolves Knowledge evidence for the operation or reuses the
        matching exchange supplied as `evidenceExchangeId`. If the session references a Jira issue, BA reads its
        requirements before asking the configured Foundry agent for a process draft.

        The saved draft contains steps, acceptance criteria, open questions, sources and diagram exports.
        Retry with the same `run_id` and body to reuse work already saved. `409 knowledge_snapshot_unavailable`
        indicates a snapshot selection problem. `503 agent_unavailable` indicates a Foundry configuration or
        request failure. A draft is ready for human review before publication.
        """
        return RunResponse.from_run(await service.prepare(session_id, run_id, body))

    @router.get("/{run_id}", summary="Review a saved BA run", responses=problem_responses(400, 401, 404, 503))
    async def review(session_id: UUID, run_id: UUID, service: Annotated[RunService, Depends(_service)]) -> RunResponse:
        """Read the run's status, saved draft, source references and publication details. Review the process,
        acceptance criteria and open questions. Copy `draftSha256` for approval and publication.
        """
        return RunResponse.from_run(await service.get(session_id, run_id))

    @router.post(
        "/{run_id}/figjam",
        summary="Approve a draft and claim FigJam generation",
        responses=problem_responses(400, 401, 404, 409, 503, 504),
    )
    async def claim_figjam(
        session_id: UUID, run_id: UUID, body: DraftApproval, service: Annotated[RunService, Depends(_service)]
    ) -> FigJamClaim:
        """Submit the reviewed `draftSha256` to record approval and claim diagram generation once.

        When `claimed` is true, pass the returned `arguments` to Figma MCP's `generate_diagram` tool. Use the
        returned editable board link when publishing. A repeated claim returns `claimed: false`.
        """
        run, claimed = await service.claim_figjam(session_id, run_id, body.draft_sha256)
        arguments = None
        if claimed and run.draft is not None:
            arguments = FigJamArguments(
                name=f"{run.draft.process.title[:90]} · BA {run.id.hex[:8]}", mermaid_syntax=run.draft.mermaid
            )
        return FigJamClaim(run=RunResponse.from_run(run), claimed=claimed, arguments=arguments)

    @router.put(
        "/{run_id}/publication",
        summary="Publish the approved draft to Jira",
        responses=problem_responses(400, 401, 404, 409, 503, 504),
    )
    async def publish(
        session_id: UUID, run_id: UUID, body: PublicationRequest, service: Annotated[RunService, Depends(_service)]
    ) -> RunResponse:
        """Submit the reviewed `draftSha256` and an editable FigJam `figjamUrl`. BA saves the board link and
        publishes the draft to the session's Jira issue, or creates an issue in the configured project.

        Reuse the same hash and link on retry. If Jira's create result is uncertain, BA looks up the existing
        issue on retry. A successful response includes the Jira issue and `published` status.
        """
        return RunResponse.from_run(await service.publish(session_id, run_id, body.draft_sha256, str(body.figjam_url)))

    @router.get(
        "/{run_id}/artifacts/{name}",
        summary="Download a BA run artifact",
        responses={
            200: {
                "description": "The requested artifact as a downloadable attachment.",
                "model": RunResponse,
                "content": {
                    "application/xml": {"schema": {"type": "string"}},
                    "text/plain": {"schema": {"type": "string"}},
                },
                "headers": {"Content-Disposition": {"schema": {"type": "string"}}},
            },
            **problem_responses(400, 401, 404, 409, 503),
        },
    )
    async def artifact(
        session_id: UUID,
        run_id: UUID,
        name: Literal["flow.json", "process.bpmn", "process.mmd"],
        service: Annotated[RunService, Depends(_service)],
    ) -> Response:
        """Download `flow.json` for the saved run, `process.bpmn` for the BPMN XML, or `process.mmd` for the
        Mermaid source. The run must have a draft. Before that it returns `409 run_not_ready`.
        """
        run = await service.get(session_id, run_id)
        if run.draft is None:
            raise RunNotReadyError
        headers = {"Content-Disposition": f'attachment; filename="{name}"'}
        if name == "flow.json":
            return Response(
                RunResponse.from_run(run).model_dump_json(by_alias=True), media_type="application/json", headers=headers
            )
        if name == "process.bpmn":
            return Response(run.draft.bpmn, media_type="application/xml", headers=headers)
        return Response(run.draft.mermaid, media_type="text/plain", headers=headers)

    @router.get(
        "/{run_id}/handoff",
        summary="Read the published run for QA",
        responses=problem_responses(400, 401, 404, 409, 503),
    )
    async def handoff(session_id: UUID, run_id: UUID, service: Annotated[RunService, Depends(_service)]) -> RunResponse:
        """Read the published process and acceptance criteria for QA, with its pinned snapshot, evidence exchange,
        sources, approval, and Jira and FigJam links. Returns `409 run_not_ready` until publication succeeds.
        """
        run = await service.get(session_id, run_id)
        if run.published_at is None:
            raise RunNotReadyError
        return RunResponse.from_run(run)

    return router
