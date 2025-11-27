"""
OpenAI LLM Provider Implementation
"""

import os
import json
from typing import Any
from openai import AsyncOpenAI

from .provider import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider implementation"""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        default_temperature: float = 0.1,
        default_max_tokens: int = 500
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        self.client = AsyncOpenAI(api_key=self.api_key)
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
        """Generate a text completion using OpenAI"""
        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature or self.default_temperature,
            max_tokens=max_tokens or self.default_max_tokens
        )

        return response.choices[0].message.content

    async def complete_json(
        self,
        prompt: str,
        schema: dict | None = None,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None
    ) -> dict:
        """Generate a JSON completion using OpenAI's JSON mode"""
        messages = []

        # Add schema hint to system message if provided
        if system:
            if schema:
                system = f"{system}\n\nRespond with valid JSON matching this schema: {json.dumps(schema)}"
            messages.append({"role": "system", "content": system})
        elif schema:
            messages.append({
                "role": "system",
                "content": f"Respond with valid JSON matching this schema: {json.dumps(schema)}"
            })

        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature or self.default_temperature,
            max_tokens=max_tokens or self.default_max_tokens,
            response_format={"type": "json_object"}
        )

        return self._parse_json_response(response.choices[0].message.content)
