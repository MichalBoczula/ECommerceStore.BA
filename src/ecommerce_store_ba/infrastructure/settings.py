from re import fullmatch

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BA_")
    api_key: SecretStr = SecretStr("")
    mongodb_uri: SecretStr = SecretStr("mongodb://localhost:27017")
    mongodb_database: str = "ecommerce_store_ba"
    knowledge_api_url: AnyHttpUrl | None = None
    knowledge_api_key: SecretStr = SecretStr("")
    foundry_project_endpoint: AnyHttpUrl | None = None
    foundry_agent_name: str = Field(default="ecommerce-business-analyst", min_length=1, max_length=63)
    foundry_agent_version: str | None = Field(default=None, min_length=1, max_length=64)
    foundry_max_output_tokens: int = Field(default=6000, ge=256, le=16000)
    jira_site_url: AnyHttpUrl | None = None
    jira_api_url: AnyHttpUrl | None = None
    jira_email: str = ""
    jira_api_token: SecretStr = SecretStr("")
    jira_project_key: str | None = Field(default=None, pattern=r"^[A-Z][A-Z0-9_]*$")
    jira_issue_type_id: str | None = Field(default=None, pattern=r"^[0-9]+$")

    @field_validator("foundry_project_endpoint", "jira_site_url", "jira_api_url")
    @classmethod
    def validate_provider_url(cls, url: AnyHttpUrl | None) -> AnyHttpUrl | None:
        if url is not None and (
            url.scheme != "https" or url.username is not None or url.query is not None or url.fragment is not None
        ):
            raise ValueError("Provider URL must use HTTPS and contain no credentials, query or fragment.")
        return url

    @field_validator("foundry_project_endpoint")
    @classmethod
    def validate_foundry_project(cls, url: AnyHttpUrl | None) -> AnyHttpUrl | None:
        if url is not None and (
            not (url.host or "").endswith(".services.ai.azure.com")
            or not fullmatch(r"/api/projects/[A-Za-z0-9_-]+/?", url.path or "")
        ):
            raise ValueError("Supply the Azure Foundry project endpoint.")
        return url
