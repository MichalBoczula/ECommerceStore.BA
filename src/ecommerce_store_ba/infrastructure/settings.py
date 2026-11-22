from pydantic import AnyHttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BA_")
    api_key: SecretStr = SecretStr("")
    mongodb_uri: SecretStr = SecretStr("mongodb://localhost:27017")
    mongodb_database: str = "ecommerce_store_ba"
    knowledge_api_url: AnyHttpUrl | None = None
    knowledge_api_key: SecretStr = SecretStr("")
