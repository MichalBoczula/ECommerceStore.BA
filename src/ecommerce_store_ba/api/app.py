from collections.abc import AsyncGenerator
from contextlib import AsyncExitStack, asynccontextmanager
from hmac import compare_digest
from typing import Annotated, Any, cast
from uuid import UUID

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from fastapi import APIRouter, Depends, FastAPI, Security
from fastapi.security import APIKeyHeader
from httpx2 import AsyncBaseTransport, AsyncClient, BasicAuth
from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError
from starlette.requests import Request

from ecommerce_store_ba.api.contracts import (
    CaptureExchangeRequest,
    CreateSessionRequest,
    EvidenceRequest,
    ExchangeResponse,
    SessionResponse,
)
from ecommerce_store_ba.api.errors import (
    BAD_REQUEST,
    PROBLEM_MEDIA_TYPE,
    UNAUTHORIZED,
    UNAVAILABLE,
    RequestProblem,
    install_error_handlers,
    problem_responses,
)
from ecommerce_store_ba.api.runs import run_router
from ecommerce_store_ba.application.evidence_service import EvidenceService
from ecommerce_store_ba.application.ports import SessionRepository
from ecommerce_store_ba.application.run_models import JiraPublisher, ProcessAgent, RunRepository
from ecommerce_store_ba.application.run_service import RunService
from ecommerce_store_ba.application.session_service import CaptureExchange, SessionService, canonical_json
from ecommerce_store_ba.infrastructure.foundry_client import FOUNDRY_SCOPE, FoundryProcessAgent
from ecommerce_store_ba.infrastructure.jira_client import JiraClient
from ecommerce_store_ba.infrastructure.knowledge_client import KnowledgeClient
from ecommerce_store_ba.infrastructure.mongo_repository import Document, MongoSessionRepository
from ecommerce_store_ba.infrastructure.mongo_runs import MongoRunRepository
from ecommerce_store_ba.infrastructure.settings import Settings

key_header = APIKeyHeader(name="X-Api-Key", auto_error=False)


def create_app(
    settings: Settings | None = None,
    repository: SessionRepository | None = None,
    *,
    knowledge_transport: AsyncBaseTransport | None = None,
    run_repository: RunRepository | None = None,
    agent: ProcessAgent | None = None,
    jira: JiraPublisher | None = None,
) -> FastAPI:
    config = settings or Settings()
    expected_key = config.api_key.get_secret_value().encode()
    if not expected_key:
        raise ValueError("BA_API_KEY must be configured")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        async with AsyncExitStack() as stack:
            store = repository
            runs = run_repository
            if store is None:
                client = await stack.enter_async_context(
                    AsyncMongoClient[Document](config.mongodb_uri.get_secret_value(), tz_aware=True, timeoutMS=3000)
                )
                app.state.mongo = client
                database = client[config.mongodb_database]
                store = MongoSessionRepository(database)
                if runs is None:
                    runs = MongoRunRepository(database)
            sessions = SessionService(store)
            app.state.session_service = sessions
            knowledge = None
            if config.knowledge_api_url is not None and config.knowledge_api_key.get_secret_value():
                upstream = await stack.enter_async_context(
                    AsyncClient(
                        base_url=str(config.knowledge_api_url),
                        headers={"X-Api-Key": config.knowledge_api_key.get_secret_value()},
                        timeout=30,
                        follow_redirects=False,
                        transport=knowledge_transport,
                    )
                )
                knowledge = KnowledgeClient(upstream)
            evidence = EvidenceService(sessions, knowledge)
            app.state.evidence_service = evidence
            app.state.run_service = (
                RunService(
                    sessions, evidence, runs, agent or await _foundry(config, stack), jira or await _jira(config, stack)
                )
                if runs is not None
                else None
            )
            yield

    app = FastAPI(title="ECommerce Store BA", docs_url="/swagger", lifespan=lifespan)
    install_error_handlers(app)

    async def authorize(key: Annotated[str | None, Security(key_header)]) -> None:
        if key is None or not compare_digest(expected_key, key.encode()):
            raise RequestProblem(UNAUTHORIZED)

    def session_service(request: Request) -> SessionService:
        return cast(SessionService, request.app.state.session_service)

    def evidence_service(request: Request) -> EvidenceService:
        return cast(EvidenceService, request.app.state.evidence_service)

    router = APIRouter(prefix="/api/v1/sessions", tags=["Sessions"], dependencies=[Depends(authorize)])

    @app.get("/health/live", tags=["Health"])
    async def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["Health"], responses=problem_responses(503))
    async def ready(request: Request) -> dict[str, str]:
        if repository is None:
            client = cast(AsyncMongoClient[Document], request.app.state.mongo)
            try:
                await client.admin.command("ping")
            except PyMongoError as error:
                raise RequestProblem(UNAVAILABLE) from error
        return {"status": "ok"}

    @router.post("", status_code=201, responses=problem_responses(400, 401, 503))
    async def create_session(
        body: CreateSessionRequest, service: Annotated[SessionService, Depends(session_service)]
    ) -> SessionResponse:
        return SessionResponse.from_domain(await service.create(body.operation, body.jira_issue_key, body.snapshot_id))

    @router.get("/{session_id}", responses=problem_responses(400, 401, 404, 503))
    async def get_session(
        session_id: UUID, service: Annotated[SessionService, Depends(session_service)]
    ) -> SessionResponse:
        return SessionResponse.from_domain(await service.get(session_id))

    @router.put("/{session_id}/exchanges/{exchange_id}", responses=problem_responses(400, 401, 404, 409, 413, 503))
    async def capture_exchange(
        session_id: UUID,
        exchange_id: UUID,
        body: CaptureExchangeRequest,
        service: Annotated[SessionService, Depends(session_service)],
    ) -> ExchangeResponse:
        try:
            request_json = canonical_json(body.request)
            response_json = canonical_json(body.response)
        except (ValueError, RecursionError) as error:
            raise RequestProblem(BAD_REQUEST) from error
        capture = CaptureExchange(body.source, request_json, response_json, body.model)
        return ExchangeResponse.from_domain(await service.capture(session_id, exchange_id, capture))

    @router.get("/{session_id}/exchanges/{exchange_id}", responses=problem_responses(400, 401, 404, 503))
    async def get_exchange(
        session_id: UUID, exchange_id: UUID, service: Annotated[SessionService, Depends(session_service)]
    ) -> ExchangeResponse:
        return ExchangeResponse.from_domain(await service.get_exchange(session_id, exchange_id))

    @router.put("/{session_id}/evidence/{exchange_id}", responses=problem_responses(400, 401, 404, 409, 413, 502, 503))
    async def resolve_evidence(
        session_id: UUID,
        exchange_id: UUID,
        body: EvidenceRequest,
        service: Annotated[EvidenceService, Depends(evidence_service)],
    ) -> ExchangeResponse:
        exchange = await service.resolve(session_id, exchange_id, body.service, body.method, body.path)
        return ExchangeResponse.from_domain(exchange)

    app.include_router(router)
    app.include_router(run_router(authorize))
    original_openapi = app.openapi

    def openapi() -> dict[str, Any]:
        schema = original_openapi()
        for path in schema["paths"].values():
            for operation in path.values():
                responses = operation["responses"]
                responses.pop("422", None)
                for status, response in responses.items():
                    if int(status) >= 400 and "application/json" in response.get("content", {}):
                        content = response["content"]
                        content[PROBLEM_MEDIA_TYPE] = content.pop("application/json")
        return schema

    app.openapi = openapi
    return app


async def _foundry(config: Settings, stack: AsyncExitStack) -> ProcessAgent | None:
    if config.foundry_project_endpoint is None or config.foundry_agent_version is None:
        return None
    credential = stack.enter_context(DefaultAzureCredential())
    client = await stack.enter_async_context(
        AsyncClient(base_url=str(config.foundry_project_endpoint).rstrip("/") + "/", timeout=90, follow_redirects=False)
    )
    return FoundryProcessAgent(
        client,
        get_bearer_token_provider(credential, FOUNDRY_SCOPE),
        config.foundry_agent_name,
        config.foundry_agent_version,
        config.foundry_max_output_tokens,
    )


async def _jira(config: Settings, stack: AsyncExitStack) -> JiraPublisher | None:
    if config.jira_site_url is None or config.jira_project_key is None or config.jira_issue_type_id is None:
        return None
    token = config.jira_api_token.get_secret_value()
    if not config.jira_email or not token:
        return None
    client = await stack.enter_async_context(
        AsyncClient(
            base_url=str(config.jira_api_url or config.jira_site_url).rstrip("/") + "/rest/api/3/",
            auth=BasicAuth(config.jira_email, token),
            timeout=25,
            follow_redirects=False,
        )
    )
    return JiraClient(client, str(config.jira_site_url), config.jira_project_key, config.jira_issue_type_id)
