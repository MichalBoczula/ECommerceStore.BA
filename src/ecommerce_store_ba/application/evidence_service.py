from typing import Literal
from uuid import UUID

from ecommerce_store_ba.application.knowledge import (
    Answer,
    Catalog,
    ContractSection,
    EvidenceBundle,
    KnowledgeAssistant,
    KnowledgeResponseError,
    KnowledgeSnapshotError,
    KnowledgeUnavailableError,
    ScenarioSection,
    Source,
    ValidationRule,
    ValidationSection,
)
from ecommerce_store_ba.application.session_service import (
    CaptureExchange,
    ExchangeConflictError,
    ExchangeNotFoundError,
    SessionService,
    canonical_json,
)
from ecommerce_store_ba.domain.session import Exchange, ExchangeSource


class EvidenceService:
    def __init__(self, sessions: SessionService, knowledge: KnowledgeAssistant | None) -> None:
        self._sessions = sessions
        self._knowledge = knowledge

    async def resolve(self, session_id: UUID, exchange_id: UUID, service: str, method: str, path: str) -> Exchange:
        session = await self._sessions.get(session_id)
        operation = f"{method} {path}"
        # Knowledge API supplies operation-linked rules and Allure examples through its two lookup forms.
        questions = (f"{operation} contract and validation", operation)
        request_json = canonical_json(
            {"kind": "operation-evidence", "service": service, "method": method, "path": path, "questions": questions}
        )
        try:
            existing = await self._sessions.get_exchange(session_id, exchange_id)
        except ExchangeNotFoundError:
            pass
        else:
            return _reuse(existing, request_json)
        if self._knowledge is None:
            raise KnowledgeUnavailableError

        catalog = await self._knowledge.catalog()
        snapshot_id = _select_snapshot(catalog, service, session.snapshot_id)
        if session.snapshot_id is None:
            pinned = await self._sessions.pin_snapshot(session_id, snapshot_id)
            snapshot_id = _select_snapshot(catalog, service, pinned.snapshot_id)

        answers = [await self._knowledge.query(question, service, snapshot_id) for question in questions]
        bundle = _collect_evidence(answers, service, snapshot_id, method, path)
        capture = CaptureExchange(
            ExchangeSource.RAG, request_json, canonical_json(bundle.model_dump(mode="json", by_alias=True)), None
        )
        try:
            return await self._sessions.capture(session_id, exchange_id, capture)
        except ExchangeConflictError:
            # A concurrent lookup of the same request can have different provider request IDs.
            return _reuse(await self._sessions.get_exchange(session_id, exchange_id), request_json)


def _reuse(existing: Exchange, request_json: str) -> Exchange:
    if existing.source != ExchangeSource.RAG or existing.request_json != request_json:
        raise ExchangeConflictError
    return existing


def _select_snapshot(catalog: Catalog, service: str, pinned_id: str | None) -> str:
    candidates = [
        snapshot.id
        for snapshot in catalog.snapshots
        if not snapshot.is_demo and service in snapshot.services and pinned_id in (None, snapshot.id)
    ]
    if len(candidates) != 1:
        raise KnowledgeSnapshotError
    return candidates[0]


def _collect_evidence(answers: list[Answer], service: str, snapshot_id: str, method: str, path: str) -> EvidenceBundle:
    contract: ContractSection | None = None
    scenarios: list[ScenarioSection] = []
    validation_rules: list[ValidationRule] = []
    sources: dict[str, Source] = {}
    limitations: list[str] = []
    for answer in answers:
        if answer.is_demo or (answer.service, answer.snapshot_id) != (service, snapshot_id):
            raise KnowledgeResponseError
        limitations.extend(answer.limitations)
        by_id = {source.id: source for source in answer.sources}
        if len(by_id) != len(answer.sources) or any(
            (source.service, source.snapshot_id) != (service, snapshot_id) for source in answer.sources
        ):
            raise KnowledgeResponseError

        matches = [
            section
            for section in answer.sections
            if isinstance(section, ContractSection) and (section.method.upper(), section.path) == (method, path)
        ]
        if not matches:
            limitations.append(f"Evidence without a matching contract for {method} {path} was omitted.")
            continue
        if len(matches) != 1 or (contract is not None and contract.operation_id != matches[0].operation_id):
            raise KnowledgeResponseError
        contract = contract or matches[0]
        _add_sources(sources, by_id, matches[0].source_ids)
        for section in answer.sections:
            if isinstance(section, ScenarioSection):
                _add_sources(sources, by_id, section.source_ids)
                if section not in scenarios:
                    scenarios.append(section)
            elif isinstance(section, ValidationSection):
                for rule in section.rules:
                    _add_sources(sources, by_id, rule.source_ids)
                    if rule not in validation_rules:
                        validation_rules.append(rule)

    missing: list[Literal["api_contract", "scenario", "validation"]] = []
    if contract is None:
        missing.append("api_contract")
    if not scenarios:
        missing.append("scenario")
    if not validation_rules:
        missing.append("validation")
    return EvidenceBundle(
        service=service,
        snapshot_id=snapshot_id,
        contract=contract,
        scenarios=scenarios,
        validation_rules=validation_rules,
        sources=list(sources.values()),
        missing_evidence=missing,
        limitations=list(dict.fromkeys(limitations)),
        knowledge_request_ids=[answer.request_id for answer in answers],
    )


def _add_sources(sources: dict[str, Source], available: dict[str, Source], source_ids: list[str]) -> None:
    if not source_ids or any(source_id not in available for source_id in source_ids):
        raise KnowledgeResponseError
    for source_id in source_ids:
        source = available[source_id]
        if sources.setdefault(source_id, source) != source:
            raise KnowledgeResponseError
