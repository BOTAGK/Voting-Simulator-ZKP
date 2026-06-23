"""Application configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ZKP Voting Simulator"
    database_url: str = "sqlite:///./data/zkp_voting.db"
    zkp_artifacts_dir: str = "./zkp_artifacts"

    admin_username: str
    admin_password: str 
    session_secret_key: str

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
