"""LLM client using OpenAI-compatible API."""

from __future__ import annotations

from typing import Any

from openai import OpenAI

from aiir.config import LLMConfig


class LLMClient:
    """Client for OpenAI-compatible LLM APIs.

    Supports any endpoint that implements the OpenAI chat completions API,
    including OpenAI, Azure OpenAI, Ollama, and other compatible services.
    """

    def __init__(self, config: LLMConfig) -> None:
        """Initialize the LLM client.

        Args:
            config: LLM configuration including base_url, api_key, and model.
        """
        self.config = config
        self._client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
        )

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Send a chat completion request and return the response text.

        Args:
            system_prompt: System message to set context and behavior.
            user_prompt: User message containing the request.
            response_format: Optional response format dict (e.g. {"type": "json_object"}).

        Returns:
            The model's response as a string.
        """
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if response_format is not None:
            kwargs["response_format"] = response_format

        response = self._client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        """Request JSON output from the LLM.

        Enables JSON mode which ensures the model outputs valid JSON.

        Args:
            system_prompt: System message (should describe the expected JSON schema).
            user_prompt: User message containing the request.

        Returns:
            The model's JSON response as a string.
        """
        return self.complete(
            system_prompt,
            user_prompt,
            response_format={"type": "json_object"},
        )
