from asyncio import timeout
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from json import loads
from typing import cast
from uuid import UUID, uuid4, uuid5

from pydantic import ValidationError

from ecommerce_store_ba.application.diagrams import bpmn_xml, mermaid_flowchart
from ecommerce_store_ba.application.evidence_service import EvidenceService
from ecommerce_store_ba.application.knowledge import EvidenceBundle
from ecommerce_store_ba.application.run_errors import (
    AgentResponseError,
    AgentUnavailableError,
    JiraPublicationPendingError,
    JiraRejectedError,
    JiraUnavailableError,
    RunBusyError,
    RunConflictError,
    RunEvidenceError,
    RunNotFoundError,
    RunNotReadyError,
)
from ecommerce_store_ba.application.run_models import Draft, JiraPublisher, ProcessAgent, Run, RunRepository, RunRequest
from ecommerce_store_ba.application.session_service import SessionService
from ecommerce_store_ba.domain.session import ExchangeSource


class RunService:
    def __init__(
        self,
        sessions: SessionService,
        evidence: EvidenceService,
        runs: RunRepository,
        agent: ProcessAgent | None,
        jira: JiraPublisher | None,
    ) -> None:
        self._sessions = sessions
        self._evidence = evidence
        self._runs = runs
        self._agent = agent
        self._jira = jira

    async def get(self, session_id: UUID, run_id: UUID) -> Run:
        await self._sessions.get(session_id)
        run = await self._runs.get(session_id, run_id)
        if run is None:
            raise RunNotFoundError
        return run

    async def prepare(self, session_id: UUID, run_id: UUID, request: RunRequest) -> Run:
        session = await self._sessions.get(session_id)
        run = await self._runs.put(Run(id=run_id, session_id=session_id, request=request, created_at=datetime.now(UTC)))
        if run.request != request:
            raise RunConflictError
        if run.draft is not None:
            return run
        if self._agent is None:
            raise AgentUnavailableError
        async with self._claim(run) as (run, token):
            if run.draft is not None:
                return run
            exchange_id, evidence = await self._load_evidence(run)
            jira_context = None
            if session.jira_issue_key is not None:
                if self._jira is None:
                    raise JiraUnavailableError
                jira_context = await self._jira.context(session.jira_issue_key)
            process, receipt = await self._agent.draft(evidence, jira_context)
            source_ids = {source.id for source in evidence.sources}
            if jira_context is not None:
                source_ids.add(jira_context.source_id)
            try:
                process.check_sources(source_ids)
            except ValueError:
                raise AgentResponseError from None
            draft = Draft(
                process=process,
                snapshot_id=evidence.snapshot_id,
                evidence_exchange_id=exchange_id,
                sources=evidence.sources,
                missing_evidence=list(evidence.missing_evidence),
                limitations=evidence.limitations,
                jira_context=jira_context,
                agent=receipt,
                bpmn=bpmn_xml(process),
                mermaid=mermaid_flowchart(process),
            )
            return await self._save(run.model_copy(update={"draft": draft}), token)

    async def _load_evidence(self, run: Run) -> tuple[UUID, EvidenceBundle]:
        request = run.request
        exchange_id = request.evidence_exchange_id or uuid5(run.id, "operation-evidence")
        if request.evidence_exchange_id is None:
            exchange = await self._evidence.resolve(
                run.session_id, exchange_id, request.service, request.method, request.path
            )
        else:
            exchange = await self._sessions.get_exchange(run.session_id, exchange_id)
        saved_request = loads(exchange.request_json)
        if exchange.source != ExchangeSource.RAG or not isinstance(saved_request, dict):
            raise RunEvidenceError
        operation = {
            "kind": "operation-evidence",
            "service": request.service,
            "method": request.method,
            "path": request.path,
        }
        captured = cast(dict[str, object], saved_request)
        if any(captured.get(key) != value for key, value in operation.items()):
            raise RunEvidenceError
        try:
            evidence = EvidenceBundle.model_validate_json(exchange.response_json)
        except ValidationError:
            raise RunEvidenceError from None
        session = await self._sessions.get(run.session_id)
        contract = evidence.contract
        if (
            evidence.snapshot_id != session.snapshot_id
            or evidence.service != request.service
            or not evidence.sources
            or any(
                (source.service, source.snapshot_id) != (request.service, evidence.snapshot_id)
                for source in evidence.sources
            )
            or contract is None
            or (contract.method.upper(), contract.path) != (request.method, request.path)
        ):
            raise RunEvidenceError
        return exchange_id, evidence

    async def claim_figjam(self, session_id: UUID, run_id: UUID, draft_sha256: str) -> tuple[Run, bool]:
        run = await self.get(session_id, run_id)
        self._check_draft(run, draft_sha256)
        if run.figjam_requested_at is not None or run.figjam_url is not None:
            return run, False
        async with self._claim(run) as (run, token):
            if run.figjam_requested_at is not None or run.figjam_url is not None:
                return run, False
            now = datetime.now(UTC)
            run = run.model_copy(update={"approved_at": now, "figjam_requested_at": now})
            return await self._save(run, token), True

    async def publish(self, session_id: UUID, run_id: UUID, draft_sha256: str, figjam_url: str) -> Run:
        run = await self.get(session_id, run_id)
        self._check_draft(run, draft_sha256)
        if run.figjam_url not in (None, figjam_url):
            raise RunConflictError
        if run.published_at is not None:
            return run
        async with self._claim(run) as (run, token):
            if run.figjam_url not in (None, figjam_url):
                raise RunConflictError
            if run.published_at is not None:
                return run
            if run.figjam_url is None:
                run = await self._save(
                    run.model_copy(
                        update={"figjam_url": figjam_url, "approved_at": run.approved_at or datetime.now(UTC)}
                    ),
                    token,
                )
            return await self._publish_jira(run, token)

    async def _publish_jira(self, run: Run, token: UUID) -> Run:
        if self._jira is None:
            raise JiraUnavailableError
        session = await self._sessions.get(run.session_id)
        if session.jira_issue_key is not None:
            issue = await self._jira.update_issue(session.jira_issue_key, run)
        elif run.jira_requested_at is not None:
            issue = await self._jira.find_created_issue(run)
            if issue is None:
                raise JiraPublicationPendingError
        else:
            run = await self._save(run.model_copy(update={"jira_requested_at": datetime.now(UTC)}), token)
            try:
                issue = await self._jira.create_issue(run)
            except JiraRejectedError:
                await self._save(run.model_copy(update={"jira_requested_at": None}), token)
                raise
        return await self._save(run.model_copy(update={"jira_issue": issue, "published_at": datetime.now(UTC)}), token)

    def _check_draft(self, run: Run, expected: str) -> None:
        if run.draft is None:
            raise RunNotReadyError
        if run.draft.checksum != expected:
            raise RunConflictError

    async def _save(self, run: Run, token: UUID) -> Run:
        await self._runs.save(run, token)
        return run

    @asynccontextmanager
    async def _claim(self, run: Run) -> AsyncGenerator[tuple[Run, UUID]]:
        token = uuid4()
        now = datetime.now(UTC)
        claimed = await self._runs.claim(run.session_id, run.id, token, now, now + timedelta(minutes=5))
        if claimed is None:
            raise RunBusyError
        try:
            async with timeout(180):
                yield claimed, token
        finally:
            await self._runs.release(run.session_id, run.id, token)
