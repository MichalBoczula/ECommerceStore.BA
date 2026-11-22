from argparse import ArgumentParser
from json import dumps
from os import getenv
from uuid import UUID

from httpx2 import Client, RequestError


def main() -> None:
    parser = ArgumentParser(description="Prepare, review and publish a run in the BA API.")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("session")
    create.add_argument("--jira-issue-key")
    create.add_argument("--snapshot-id")
    for name in ("prepare", "review", "figjam", "publish", "handoff"):
        command = commands.add_parser(name)
        command.add_argument("session_id", type=UUID)
        command.add_argument("run_id", type=UUID)
        if name == "prepare":
            command.add_argument("service")
            command.add_argument("method")
            command.add_argument("path")
            command.add_argument("--evidence-exchange-id", type=UUID)
        if name in ("figjam", "publish"):
            command.add_argument("draft_sha256")
        if name == "publish":
            command.add_argument("figjam_url")
    options = parser.parse_args()
    key = getenv("BA_API_KEY")
    if not key:
        parser.error("Set BA_API_KEY in the environment.")
    root = "/api/v1/sessions"
    payload: dict[str, str | None] | None = None
    if options.command == "session":
        method, path = "POST", root
        payload = {"operation": "model-flow", "jiraIssueKey": options.jira_issue_key, "snapshotId": options.snapshot_id}
    else:
        path = f"{root}/{options.session_id}/runs/{options.run_id}"
        method = "GET"
        if options.command == "prepare":
            method = "PUT"
            payload = {"service": options.service, "method": options.method.upper(), "path": options.path}
            if options.evidence_exchange_id is not None:
                payload["evidenceExchangeId"] = str(options.evidence_exchange_id)
        if options.command == "figjam":
            method, path = "POST", f"{path}/figjam"
            payload = {"draftSha256": options.draft_sha256}
        if options.command == "publish":
            method, path = "PUT", f"{path}/publication"
            payload = {"draftSha256": options.draft_sha256, "figjamUrl": options.figjam_url}
        if options.command == "handoff":
            path += "/handoff"
    with Client(base_url=getenv("BA_BASE_URL", "http://localhost:8082"), timeout=195, follow_redirects=False) as client:
        try:
            response = client.request(method, path, headers={"X-Api-Key": key}, json=payload)
        except RequestError:
            raise SystemExit("BA request did not complete. Repeat with the same run ID.") from None
        try:
            result = response.json()
        except ValueError:
            raise SystemExit(f"BA returned HTTP {response.status_code} with no JSON result.") from None
        print(dumps(result, ensure_ascii=True, indent=2))
        if not response.is_success:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
