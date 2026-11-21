from typing import Annotated, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, JsonValue
from pydantic.alias_generators import to_camel


class KnowledgeUnavailableError(Exception):
    pass


class KnowledgeSnapshotError(Exception):
    pass


class KnowledgeResponseError(Exception):
    pass


class KnowledgeModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True, strict=True)


class Snapshot(KnowledgeModel):
    id: str
    is_demo: bool
    services: list[str]


class Catalog(KnowledgeModel):
    schema_version: Literal[1] = 1
    snapshots: list[Snapshot]


class Source(KnowledgeModel):
    id: str
    service: str
    snapshot_id: str
    title: str
    url: str | None = None
    path: str
    commit_sha: str
    bundle_sha256: str


class CitedSection(KnowledgeModel):
    title: str
    source_ids: list[str]


class ContractSection(CitedSection):
    type: Literal["api_contract"]
    method: str
    path: str
    operation_id: str
    media_type: str
    request_schema: dict[str, JsonValue]
    reference_schemas: dict[str, JsonValue]
    example_request: JsonValue
    example_origin: Literal["openapi", "generated", "unavailable"]
    example_schema_valid: bool | None


class ScenarioSection(CitedSection):
    type: Literal["scenario"]
    content: str
    execution_status: str | None = None


class ValidationRule(KnowledgeModel):
    field: str
    description: str
    source_ids: list[str]


class ValidationSection(CitedSection):
    type: Literal["validation"]
    rules: list[ValidationRule]


class ExplanationSection(CitedSection):
    type: Literal["explanation"]


type Section = Annotated[
    ContractSection | ScenarioSection | ValidationSection | ExplanationSection, Field(discriminator="type")
]


class Answer(KnowledgeModel):
    schema_version: Literal[1] = 1
    request_id: str
    service: str
    snapshot_id: str
    is_demo: bool
    sections: list[Section]
    sources: list[Source]
    limitations: list[str]


class EvidenceBundle(KnowledgeModel):
    schema_version: Literal[1] = 1
    service: str
    snapshot_id: str
    contract: ContractSection | None
    scenarios: list[ScenarioSection]
    validation_rules: list[ValidationRule]
    sources: list[Source]
    missing_evidence: list[Literal["api_contract", "scenario", "validation"]]
    limitations: list[str]
    knowledge_request_ids: list[str]


class KnowledgeAssistant(Protocol):
    async def catalog(self) -> Catalog: ...
    async def query(self, question: str, service: str, snapshot_id: str) -> Answer: ...
