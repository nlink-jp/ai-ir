"""Configuration management for ai-ir using pydantic-settings."""

from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseSettings):
    """LLM endpoint configuration. Reads from AIIR_LLM_* environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="AIIR_LLM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "gpt-4o"

    @field_validator("api_key")
    @classmethod
    def api_key_must_not_be_empty(cls, v: str) -> str:
        """Validate that api_key is set (may be checked at usage time)."""
        return v


class Config(BaseSettings):
    """Top-level configuration container."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm: LLMConfig = LLMConfig()


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Return the singleton Config instance, loaded from environment."""
    return Config()


def get_llm_config() -> LLMConfig:
    """Return LLM configuration, raising a helpful error if api_key is not set.

    Key resolution order:
    1. ``AIIR_LLM_API_KEY`` environment variable (or ``.env`` file).
    2. System keyring (macOS Keychain, SecretService, Windows Credential Manager)
       — populated via ``aiir config set-key``.

    Raises:
        ValueError: If the API key cannot be found through either method.
    """
    config = get_config().llm
    if config.api_key:
        return config

    # Fallback: try system keyring (macOS Keychain etc.)
    from aiir.keychain import get_api_key

    keyring_key = get_api_key()
    if keyring_key:
        return LLMConfig(
            base_url=config.base_url,
            api_key=keyring_key,
            model=config.model,
        )

    raise ValueError(
        "AIIR_LLM_API_KEY is not configured.\n"
        "Option 1 — Environment variable:  export AIIR_LLM_API_KEY=<key>\n"
        "Option 2 — .env file:             copy .env.example to .env and fill in the key\n"
        "Option 3 — System keychain:       aiir config set-key"
    )
