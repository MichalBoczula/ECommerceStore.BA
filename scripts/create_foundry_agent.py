from argparse import ArgumentParser
from json import dumps
from pathlib import Path
from typing import cast

from azure.identity import DefaultAzureCredential
from httpx2 import Client

from ecommerce_store_ba.infrastructure.foundry_client import FOUNDRY_SCOPE
from ecommerce_store_ba.infrastructure.settings import Settings


def main() -> None:
    parser = ArgumentParser(description="Create a version of the BA prompt agent in the configured Foundry project.")
    parser.add_argument("--deployment", default="gpt-6-luna")
    arguments = parser.parse_args()
    settings = Settings()
    if settings.foundry_project_endpoint is None:
        parser.error("Set BA_FOUNDRY_PROJECT_ENDPOINT.")
    prompt = (Path(__file__).resolve().parents[1] / "prompts" / "process-agent.md").read_text(encoding="utf-8")
    with DefaultAzureCredential() as credential, Client(timeout=40) as client:
        response = client.post(
            f"{str(settings.foundry_project_endpoint).rstrip('/')}/agents",
            params={"api-version": "v1"},
            headers={"Authorization": f"Bearer {credential.get_token(FOUNDRY_SCOPE).token}"},
            json={
                "name": settings.foundry_agent_name,
                "definition": {"kind": "prompt", "model": cast(str, arguments.deployment), "instructions": prompt},
            },
        )
        response.raise_for_status()
        created = response.json()
    latest = created.get("versions", {}).get("latest", {})
    version = latest.get("version")
    if str(created.get("name")) != settings.foundry_agent_name or not version:
        raise SystemExit("Agent creation returned no version. Read the created version in Foundry before retrying.")
    print(dumps({"BA_FOUNDRY_AGENT_NAME": settings.foundry_agent_name, "BA_FOUNDRY_AGENT_VERSION": str(version)}))


if __name__ == "__main__":
    main()
