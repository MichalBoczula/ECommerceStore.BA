from datetime import datetime
from hashlib import sha256
from typing import Literal, Protocol
from uuid import UUID

from pydantic import Field, JsonValue

from ecommerce_store_ba.application.knowledge import EvidenceBundle, Source
from ecommerce_store_ba.application.session_service import canonical_json
from ecommerce_store_ba.domain.process import ProcessDraft, ProcessModel


class OperationLookup(ProcessModel):
    service: Literal["products", "users", "invoices", "payments"]
    method: Literal["GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE", "TRACE"]
    path: str = Field(min_length=1, max_length=512, pattern=r"^/[a-zA-Z0-9_./{}%~-]*$")


class RunRequest(OperationLookup):
    evidence_exchange_id: UUID | None = None


class AgentReceipt(ProcessModel):
    name: str
    version: str
    response_id: str
    model: str


class JiraReference(ProcessModel):
    key: str
    url: str


class JiraContext(JiraReference):
    summary: str
    description: dict[str, JsonValue] | None
    updated: str

    @property
    def source_id(self) -> str:
        return f"jira:{self.key}"


class Draft(ProcessModel):
    schema_version: Literal[1] = 1
    process: ProcessDraft
    snapshot_id: str
    evidence_exchange_id: UUID
    sources: list[Source]
    missing_evidence: list[str]
    limitations: list[str]
    jira_context: JiraContext | None
    agent: AgentReceipt
    bpmn: str
    mermaid: str

    @property
    def checksum(self) -> str:
        return sha256(canonical_json(self.model_dump(mode="json", by_alias=True)).encode()).hexdigest()


class Run(ProcessModel):
    id: UUID
    session_id: UUID
    request: RunRequest
    created_at: datetime
    draft: Draft | None = None
    approved_at: datetime | None = None
    figjam_requested_at: datetime | None = None
    figjam_url: str | None = None
    jira_requested_at: datetime | None = None
    jira_issue: JiraReference | None = None
    published_at: datetime | None = None


class ProcessAgent(Protocol):
    async def draft(self, evidence: EvidenceBundle, jira: JiraContext | None) -> tuple[ProcessDraft, AgentReceipt]: ...


class JiraPublisher(Protocol):
    async def context(self, key: str) -> JiraContext: ...

    async def find_created_issue(self, run: Run) -> JiraReference | None: ...

    async def create_issue(self, run: Run) -> JiraReference: ...

    async def update_issue(self, key: str, run: Run) -> JiraReference: ...


class RunRepository(Protocol):
    async def put(self, run: Run) -> Run: ...

    async def get(self, session_id: UUID, run_id: UUID) -> Run | None: ...

    async def claim(
        self, session_id: UUID, run_id: UUID, token: UUID, now: datetime, until: datetime
    ) -> Run | None: ...

    async def save(self, run: Run, token: UUID) -> None: ...

    async def release(self, session_id: UUID, run_id: UUID, token: UUID) -> None: ...
