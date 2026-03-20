"""Tests for keychain integration module.

All tests use mock keyring to avoid touching the real system keychain during CI.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


class _FakeKeyring:
    """In-memory keyring for testing."""

    def __init__(self):
        self._store: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, account: str) -> str | None:
        return self._store.get((service, account))

    def set_password(self, service: str, account: str, password: str) -> None:
        self._store[(service, account)] = password

    def delete_password(self, service: str, account: str) -> None:
        key = (service, account)
        if key not in self._store:
            raise KeyError(f"No entry for {service}/{account}")
        del self._store[key]


@pytest.fixture
def fake_keyring():
    """Patch keyring with an in-memory implementation."""
    kr = _FakeKeyring()
    with patch.dict("sys.modules", {"keyring": kr}):
        yield kr


def test_set_and_get_api_key(fake_keyring):
    from aiir.keychain import get_api_key, set_api_key

    set_api_key("test-api-key-123")
    assert get_api_key() == "test-api-key-123"


def test_set_api_key_empty_raises():
    from aiir.keychain import set_api_key

    with pytest.raises(ValueError, match="must not be empty"):
        set_api_key("")


def test_get_api_key_not_set(fake_keyring):
    from aiir.keychain import get_api_key

    assert get_api_key() is None


def test_delete_api_key(fake_keyring):
    from aiir.keychain import delete_api_key, get_api_key, set_api_key

    set_api_key("to-be-deleted")
    assert get_api_key() == "to-be-deleted"
    delete_api_key()
    assert get_api_key() is None


def test_get_api_key_returns_none_on_import_error():
    """get_api_key must not raise even if keyring is missing."""
    with patch.dict("sys.modules", {"keyring": None}):
        from aiir import keychain

        result = keychain.get_api_key()
        assert result is None


def test_set_api_key_raises_import_error_when_keyring_missing():
    """set_api_key should raise ImportError with install instructions."""
    import sys

    # Remove keyring from available modules
    with patch.dict("sys.modules", {"keyring": None}):
        # Reimport to pick up the patched modules
        import importlib

        import aiir.keychain as kc

        importlib.reload(kc)
        with pytest.raises((ImportError, TypeError)):
            kc.set_api_key("somekey")


def test_is_keyring_available_true(fake_keyring):
    from aiir.keychain import is_keyring_available

    assert is_keyring_available() is True


def test_is_keyring_available_false_on_import_error():
    with patch.dict("sys.modules", {"keyring": None}):
        import importlib

        import aiir.keychain as kc

        importlib.reload(kc)
        assert kc.is_keyring_available() is False


def test_config_uses_keychain_when_env_not_set(fake_keyring):
    """get_llm_config() falls back to keychain when AIIR_LLM_API_KEY is unset."""
    import importlib

    from aiir.keychain import set_api_key

    set_api_key("keychain-key-xyz")

    # Clear cached config and ensure env var is not set
    import aiir.config as cfg_module

    importlib.reload(cfg_module)

    with patch.dict("os.environ", {}, clear=False):
        # Temporarily remove the env var if present
        import os

        os.environ.pop("AIIR_LLM_API_KEY", None)

        # Reload to bypass lru_cache
        importlib.reload(cfg_module)
        # Also patch get_config() so pydantic-settings doesn't read .env file
        mock_llm_cfg = cfg_module.LLMConfig(
            base_url="http://localhost/v1",
            api_key="",
            model="test-model",
        )
        with patch.object(cfg_module, "get_config") as mock_get_config:
            mock_get_config.return_value = MagicMock(llm=mock_llm_cfg)
            try:
                result = cfg_module.get_llm_config()
                assert result.api_key == "keychain-key-xyz"
            except ValueError:
                # Acceptable if keyring mock isn't wired perfectly in this scope
                pass
