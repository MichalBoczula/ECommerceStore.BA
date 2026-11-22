from httpx2 import AsyncClient, RequestError
from pydantic import BaseModel, ValidationError

from ecommerce_store_ba.application.knowledge import (
    Answer,
    Catalog,
    KnowledgeResponseError,
    KnowledgeSnapshotError,
    KnowledgeUnavailableError,
)


class KnowledgeClient:
    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def catalog(self) -> Catalog:
        return await self._request("GET", "/api/v1/catalog", Catalog)

    async def query(self, question: str, service: str, snapshot_id: str) -> Answer:
        return await self._request(
            "POST", "/api/v1/query", Answer, {"question": question, "service": service, "snapshotId": snapshot_id}
        )

    async def _request[T: BaseModel](
        self, method: str, path: str, model: type[T], payload: dict[str, str] | None = None
    ) -> T:
        try:
            response = await self._client.request(method, path, json=payload)
        except RequestError:
            raise KnowledgeUnavailableError from None
        if method == "POST" and response.status_code == 409:
            raise KnowledgeSnapshotError
        if not response.is_success:
            raise KnowledgeUnavailableError
        try:
            return model.model_validate_json(response.content)
        except ValidationError:
            raise KnowledgeResponseError from None
