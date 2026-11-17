"""Provider-agnostic LLM interface. The extractor only knows `complete(messages)`; which model
answers is decided by LLM_PROVIDER. Adding a provider = one new class + one line in factory.py."""
from dataclasses import dataclass
from typing import Protocol


@dataclass
class LLMResult:
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class LLMClient(Protocol):
    provider: str
    model: str

    async def complete(self, messages: list[dict]) -> LLMResult: ...


def parse_chat_completion(payload: dict) -> LLMResult:
    """Parse an OpenAI-style chat completion (OpenAI API and vLLM on SageMaker both return this)."""
    try:
        message = payload["choices"][0]["message"]
    except (KeyError, IndexError, TypeError):
        raise ValueError(f"Unexpected response shape: {str(payload)[:300]}")
    # gpt-oss puts its chain of thought in `reasoning_content` (vLLM) and the answer in `content`.
    text = message.get("content") or ""
    usage = payload.get("usage") or {}
    return LLMResult(
        text=text,
        input_tokens=usage.get("prompt_tokens"),
        output_tokens=usage.get("completion_tokens"),
    )
