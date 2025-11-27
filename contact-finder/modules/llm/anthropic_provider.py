"""
Anthropic Claude LLM Provider Implementation
"""

import os
import json
from typing import Any
from anthropic import AsyncAnthropic

from .provider import LLMProvider


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider implementation"""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-3-haiku-20240307",
        default_temperature: float = 0.1,
        default_max_tokens: int = 500
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not provided")

        self.client = AsyncAnthropic(api_key=self.api_key)
        self.model = model
        self.default_temperature = default_temperature
        self.default_max_tokens = default_max_tokens

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None
    ) -> str:
        """Generate a text completion using Anthropic Claude"""
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens or self.default_max_tokens,
            system=system or "",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    async def complete_json(
        self,
        prompt: str,
        schema: dict | None = None,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None
    ) -> dict:
        """Generate a JSON completion using Anthropic Claude"""
        # Anthropic doesn't have native JSON mode, so we prompt for it
        json_system = system or ""
        if schema:
            json_system = f"{json_system}\n\nYou MUST respond with valid JSON matching this schema: {json.dumps(schema)}"
        else:
            json_system = f"{json_system}\n\nYou MUST respond with valid JSON only. No markdown, no explanations."

        json_prompt = f"{prompt}\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown code blocks, no explanations."

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens or self.default_max_tokens,
            system=json_system,
            messages=[{"role": "user", "content": json_prompt}]
        )

        return self._parse_json_response(response.content[0].text)
