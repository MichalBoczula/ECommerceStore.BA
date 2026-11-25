from asyncio import to_thread
from collections.abc import Callable
from logging import getLogger
from typing import Annotated

from azure.core.exceptions import AzureError
from httpx2 import AsyncClient, RequestError
from pydantic import BaseModel, Field, ValidationError

from ecommerce_store_ba.application.knowledge import EvidenceBundle
from ecommerce_store_ba.application.run_errors import AgentResponseError, AgentUnavailableError
from ecommerce_store_ba.application.run_models import AgentReceipt, JiraContext
from ecommerce_store_ba.application.session_service import canonical_json
from ecommerce_store_ba.domain.process import ProcessDraft

FOUNDRY_SCOPE = "https://ai.azure.com/.default"
logger = getLogger(__name__)


class _Content(BaseModel):
    type: str
    text: str | None = None


class _Item(BaseModel):
    type: str
    content: list[_Content] = Field(default_factory=list[_Content])


class _Response(BaseModel):
    id: Annotated[str, Field(min_length=1)]
    model: Annotated[str, Field(min_length=1)]
    status: str
    output: list[_Item]


class FoundryProcessAgent:
    def __init__(
        self, client: AsyncClient, token: Callable[[], str], name: str, version: str, max_output_tokens: int
    ) -> None:
        self._client = client
        self._token = token
        self._name = name
        self._version = version
        self._max_output_tokens = max_output_tokens

    async def draft(self, evidence: EvidenceBundle, jira: JiraContext | None) -> tuple[ProcessDraft, AgentReceipt]:
        payload = {
            "knowledgeEvidence": evidence.model_dump(mode="json", by_alias=True),
            "jiraRequirements": (
                {"sourceId": jira.source_id, **jira.model_dump(mode="json", by_alias=True)}
                if jira is not None
                else None
            ),
        }
        # Foundry rejects text.format overrides when a saved agent is specified.
        schema = canonical_json(ProcessDraft.model_json_schema(by_alias=True))
        try:
            response = await self._client.post(
                "openai/v1/responses",
                params={"api-version": "v1"},
                headers={"Authorization": f"Bearer {await to_thread(self._token)}"},
                json={
                    "agent_reference": {"type": "agent_reference", "name": self._name, "version": self._version},
                    "input": [
                        {
                            "type": "message",
                            "role": "developer",
                            "content": (
                                "Return exactly one JSON object matching this schema, without Markdown "
                                f"or surrounding text.\n{schema}"
                            ),
                        },
                        {"type": "message", "role": "user", "content": canonical_json(payload)},
                    ],
                    "tool_choice": "none",
                    "store": False,
                    "max_output_tokens": self._max_output_tokens,
                },
            )
        except (AzureError, RequestError) as exc:
            logger.warning("Foundry process agent request failed: %s", type(exc).__name__)
            raise AgentUnavailableError from None
        if not response.is_success:
            logger.warning("Foundry process agent request failed: HTTP %s", response.status_code)
            raise AgentUnavailableError
        try:
            result = _Response.model_validate_json(response.content)
            content = [block for item in result.output if item.type == "message" for block in item.content]
            text = [block.text for block in content if block.type == "output_text" and block.text]
            if result.status != "completed" or len(text) != 1 or any(block.type == "refusal" for block in content):
                raise AgentResponseError
            draft = ProcessDraft.model_validate_json(text[0])
        except ValidationError:
            raise AgentResponseError from None
        return draft, AgentReceipt(name=self._name, version=self._version, response_id=result.id, model=result.model)
