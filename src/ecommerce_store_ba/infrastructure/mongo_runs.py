from datetime import UTC, datetime
from typing import NotRequired, TypedDict, cast
from uuid import UUID

from pymongo import ReturnDocument
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from ecommerce_store_ba.application.run_errors import RunBusyError
from ecommerce_store_ba.application.run_models import Run
from ecommerce_store_ba.infrastructure.mongo_repository import Document


class RunDocument(TypedDict):
    _id: str
    run_json: str
    lease_token: NotRequired[str]
    lease_until: NotRequired[datetime]


class JiraIssueLease(TypedDict):
    _id: str
    token: str
    until: datetime


class MongoRunRepository:
    def __init__(self, database: AsyncDatabase[Document]) -> None:
        self._collection = cast(AsyncCollection[RunDocument], database.get_collection("runs"))
        self._jira_leases = cast(AsyncCollection[JiraIssueLease], database.get_collection("jira_issue_leases"))

    async def put(self, run: Run) -> Run:
        document = RunDocument(_id=_key(run.session_id, run.id), run_json=run.model_dump_json(by_alias=True))
        try:
            await self._collection.insert_one(document)
        except DuplicateKeyError:
            existing = await self.get(run.session_id, run.id)
            if existing is None:
                raise
            return existing
        return run

    async def get(self, session_id: UUID, run_id: UUID) -> Run | None:
        document = await self._collection.find_one({"_id": _key(session_id, run_id)})
        return Run.model_validate_json(document["run_json"]) if document is not None else None

    async def claim(self, session_id: UUID, run_id: UUID, token: UUID, now: datetime, until: datetime) -> Run | None:
        document = await self._collection.find_one_and_update(
            {
                "_id": _key(session_id, run_id),
                "$or": [{"lease_until": {"$lte": now}}, {"lease_until": {"$exists": False}}],
            },
            {"$set": {"lease_token": str(token), "lease_until": until}},
            return_document=ReturnDocument.AFTER,
        )
        return Run.model_validate_json(document["run_json"]) if document is not None else None

    async def save(self, run: Run, token: UUID) -> None:
        result = await self._collection.update_one(
            {"_id": _key(run.session_id, run.id), "lease_token": str(token), "lease_until": {"$gt": datetime.now(UTC)}},
            {"$set": {"run_json": run.model_dump_json(by_alias=True)}},
        )
        if not result.matched_count:
            raise RunBusyError

    async def release(self, session_id: UUID, run_id: UUID, token: UUID) -> None:
        await self._collection.update_one(
            {"_id": _key(session_id, run_id), "lease_token": str(token)},
            {"$unset": {"lease_token": "", "lease_until": ""}},
        )

    async def claim_jira_issue(self, key: str, token: UUID, now: datetime, until: datetime) -> bool:
        lease = JiraIssueLease(_id=key, token=str(token), until=until)
        try:
            await self._jira_leases.replace_one({"_id": key, "until": {"$lte": now}}, lease, upsert=True)
        except DuplicateKeyError:
            return False
        return True

    async def release_jira_issue(self, key: str, token: UUID) -> None:
        await self._jira_leases.delete_one({"_id": key, "token": str(token)})


def _key(session_id: UUID, run_id: UUID) -> str:
    return f"{session_id}:{run_id}"
