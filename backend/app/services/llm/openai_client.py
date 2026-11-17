"""OpenAI API directly. Used on Day 1 to test real LLM extraction before SageMaker is up."""
import logging

import httpx

from ...config import Settings
from ...errors import LLMError
from .base import LLMResult, parse_chat_completion

logger = logging.getLogger("app.llm.openai")

OPENAI_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIClient:
    provider = "openai"

    def __init__(self, settings: Settings):
        if not settings.openai_api_key:
            raise RuntimeError("LLM_PROVIDER=openai but OPENAI_API_KEY is empty")
        self.settings = settings
        self.model = settings.openai_model
        self.http = httpx.AsyncClient(
            timeout=settings.llm_timeout_seconds,
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
        )

    async def complete(self, messages: list[dict]) -> LLMResult:
        body = {
            "model": self.model,
            "messages": messages,
            "response_format": {"type": "json_object"},  # forces syntactically valid JSON
            "max_completion_tokens": self.settings.llm_max_tokens,
        }
        if self.model.startswith(("gpt-5", "o")):  # reasoning models
            body["reasoning_effort"] = self.settings.llm_reasoning_effort
        try:
            response = await self.http.post(OPENAI_URL, json=body)
        except httpx.TimeoutException:
            raise LLMError("OpenAI request timed out")
        except httpx.HTTPError as exc:
            raise LLMError("Could not reach OpenAI", details=str(exc))

        if response.status_code != 200:
            logger.error("openai_error", extra={"status": response.status_code, "body": response.text[:500]})
            raise LLMError(f"OpenAI returned HTTP {response.status_code}", details=response.text[:500])
        return parse_chat_completion(response.json())
