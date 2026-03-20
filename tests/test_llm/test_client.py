"""Tests for aiir.llm.client module."""

from unittest.mock import MagicMock, patch

import pytest

from aiir.config import LLMConfig
from aiir.llm.client import LLMClient


def _make_config(**kwargs) -> LLMConfig:
    """Create an LLMConfig for testing (bypasses env var requirements)."""
    defaults = dict(base_url="http://localhost:11434/v1", api_key="test-key", model="test-model")
    defaults.update(kwargs)
    return LLMConfig(**defaults)


def _make_mock_response(content: str) -> MagicMock:
    """Create a mock OpenAI API response."""
    response = MagicMock()
    response.choices = [MagicMock(message=MagicMock(content=content))]
    return response


# ---------------------------------------------------------------------------
# LLMClient initialization
# ---------------------------------------------------------------------------


def test_client_stores_config():
    """Test that LLMClient stores the config."""
    config = _make_config()
    with patch("aiir.llm.client.OpenAI"):
        client = LLMClient(config)
    assert client.config is config


def test_client_creates_openai_with_correct_params():
    """Test that LLMClient passes base_url and api_key to OpenAI."""
    config = _make_config(base_url="http://custom-endpoint/v1", api_key="my-key")
    with patch("aiir.llm.client.OpenAI") as mock_openai_cls:
        LLMClient(config)
    mock_openai_cls.assert_called_once_with(
        api_key="my-key",
        base_url="http://custom-endpoint/v1",
    )


# ---------------------------------------------------------------------------
# complete
# ---------------------------------------------------------------------------


def test_complete_sends_correct_messages():
    """Test that complete sends system and user messages."""
    config = _make_config()

    with patch("aiir.llm.client.OpenAI") as mock_openai_cls:
        mock_openai = MagicMock()
        mock_openai_cls.return_value = mock_openai
        mock_openai.chat.completions.create.return_value = _make_mock_response('{"result": "ok"}')

        client = LLMClient(config)
        result = client.complete("system prompt", "user prompt")

    assert result == '{"result": "ok"}'
    call_kwargs = mock_openai.chat.completions.create.call_args[1]
    assert call_kwargs["model"] == "test-model"
    messages = call_kwargs["messages"]
    assert messages[0] == {"role": "system", "content": "system prompt"}
    assert messages[1] == {"role": "user", "content": "user prompt"}


def test_complete_returns_string():
    """Test that complete returns the response content as a string."""
    config = _make_config()

    with patch("aiir.llm.client.OpenAI") as mock_openai_cls:
        mock_openai = MagicMock()
        mock_openai_cls.return_value = mock_openai
        mock_openai.chat.completions.create.return_value = _make_mock_response("hello")

        client = LLMClient(config)
        result = client.complete("sys", "user")

    assert isinstance(result, str)
    assert result == "hello"


def test_complete_no_response_format_by_default():
    """Test that complete does not set response_format by default."""
    config = _make_config()

    with patch("aiir.llm.client.OpenAI") as mock_openai_cls:
        mock_openai = MagicMock()
        mock_openai_cls.return_value = mock_openai
        mock_openai.chat.completions.create.return_value = _make_mock_response("ok")

        client = LLMClient(config)
        client.complete("sys", "user")

    call_kwargs = mock_openai.chat.completions.create.call_args[1]
    assert "response_format" not in call_kwargs


def test_complete_with_response_format():
    """Test that complete passes response_format when provided."""
    config = _make_config()

    with patch("aiir.llm.client.OpenAI") as mock_openai_cls:
        mock_openai = MagicMock()
        mock_openai_cls.return_value = mock_openai
        mock_openai.chat.completions.create.return_value = _make_mock_response("{}")

        client = LLMClient(config)
        client.complete("sys", "user", response_format={"type": "json_object"})

    call_kwargs = mock_openai.chat.completions.create.call_args[1]
    assert call_kwargs["response_format"] == {"type": "json_object"}


# ---------------------------------------------------------------------------
# complete_json
# ---------------------------------------------------------------------------


def test_complete_json_sets_response_format():
    """Test that complete_json sets the JSON response format."""
    config = _make_config()

    with patch("aiir.llm.client.OpenAI") as mock_openai_cls:
        mock_openai = MagicMock()
        mock_openai_cls.return_value = mock_openai
        mock_openai.chat.completions.create.return_value = _make_mock_response("{}")

        client = LLMClient(config)
        client.complete_json("system", "user")

    call_kwargs = mock_openai.chat.completions.create.call_args[1]
    assert call_kwargs.get("response_format") == {"type": "json_object"}


def test_complete_json_returns_string():
    """Test that complete_json returns a string (not parsed JSON)."""
    config = _make_config()

    with patch("aiir.llm.client.OpenAI") as mock_openai_cls:
        mock_openai = MagicMock()
        mock_openai_cls.return_value = mock_openai
        mock_openai.chat.completions.create.return_value = _make_mock_response(
            '{"key": "value"}'
        )

        client = LLMClient(config)
        result = client.complete_json("sys", "user")

    assert isinstance(result, str)
    assert result == '{"key": "value"}'


def test_complete_json_passes_correct_messages():
    """Test that complete_json sends the correct system and user messages."""
    config = _make_config()

    with patch("aiir.llm.client.OpenAI") as mock_openai_cls:
        mock_openai = MagicMock()
        mock_openai_cls.return_value = mock_openai
        mock_openai.chat.completions.create.return_value = _make_mock_response("{}")

        client = LLMClient(config)
        client.complete_json("my system", "my user")

    call_kwargs = mock_openai.chat.completions.create.call_args[1]
    messages = call_kwargs["messages"]
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "my system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "my user"
