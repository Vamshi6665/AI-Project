"""Fallback: the same gpt-oss-20b model through Amazon Bedrock's Converse API.

Pay per token, nothing to deploy, no GPU quota. Use it if the SageMaker quota is still pending.
The EC2 role then needs bedrock:InvokeModel instead of sagemaker:InvokeEndpoint.
"""
import asyncio
import logging

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from ...config import Settings
from ...errors import LLMError
from .base import LLMResult

logger = logging.getLogger("app.llm.bedrock")


class BedrockClient:
    provider = "bedrock"

    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = settings.bedrock_model_id
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
            config=Config(read_timeout=settings.llm_timeout_seconds, retries={"max_attempts": 2, "mode": "standard"}),
        )

    def _converse(self, messages: list[dict]) -> dict:
        system = [{"text": m["content"]} for m in messages if m["role"] == "system"]
        convo = [
            {"role": m["role"], "content": [{"text": m["content"]}]}
            for m in messages
            if m["role"] in ("user", "assistant")
        ]
        return self.client.converse(
            modelId=self.model,
            system=system,
            messages=convo,
            inferenceConfig={"maxTokens": self.settings.llm_max_tokens, "temperature": 0},
        )

    async def complete(self, messages: list[dict]) -> LLMResult:
        try:
            response = await asyncio.to_thread(self._converse, messages)
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "ClientError")
            msg = exc.response.get("Error", {}).get("Message", str(exc))
            logger.error("bedrock_error", extra={"aws_code": code, "aws_message": msg[:500]})
            raise LLMError(f"Bedrock error ({code})", details=msg[:500])
        except BotoCoreError as exc:
            raise LLMError("Could not reach Bedrock", details=str(exc))

        blocks = response.get("output", {}).get("message", {}).get("content", [])
        # gpt-oss returns a reasoningContent block plus a text block; keep only the text.
        text = "".join(b["text"] for b in blocks if "text" in b)
        usage = response.get("usage", {})
        return LLMResult(text=text, input_tokens=usage.get("inputTokens"), output_tokens=usage.get("outputTokens"))
