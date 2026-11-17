"""gpt-oss-20b on a SageMaker real-time endpoint (vLLM container, OpenAI-compatible payload).

Auth: boto3 picks up credentials automatically. On EC2 they come from the instance's IAM role,
so there are no access keys in the code, the .env file or the Docker image.
"""
import asyncio
import json
import logging

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError, ReadTimeoutError

from ...config import Settings
from ...errors import LLMError
from .base import LLMResult, parse_chat_completion

logger = logging.getLogger("app.llm.sagemaker")


class SageMakerClient:
    provider = "sagemaker"

    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = settings.model_label
        self.endpoint = settings.sagemaker_endpoint_name
        self.client = boto3.client(
            "sagemaker-runtime",
            region_name=settings.aws_region,
            # Real-time endpoints cap one invocation at 60 s, so waiting longer than ~70 s is pointless.
            config=Config(read_timeout=min(settings.llm_timeout_seconds, 70), retries={"max_attempts": 2, "mode": "standard"}),
        )

    def _invoke(self, body: dict) -> dict:
        response = self.client.invoke_endpoint(
            EndpointName=self.endpoint,
            ContentType="application/json",
            Accept="application/json",
            Body=json.dumps(body),
        )
        return json.loads(response["Body"].read())

    async def complete(self, messages: list[dict]) -> LLMResult:
        body = {
            "model": "openai/gpt-oss-20b",
            "messages": messages,
            "max_tokens": self.settings.llm_max_tokens,
            "temperature": 0,
            # gpt-oss supports low/medium/high reasoning. Low is plenty for extraction and keeps latency down.
            "reasoning_effort": self.settings.llm_reasoning_effort,
        }
        try:
            payload = await asyncio.to_thread(self._invoke, body)
        except ReadTimeoutError:
            raise LLMError("SageMaker endpoint timed out. Try a shorter document or lower LLM_MAX_TOKENS.")
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "ClientError")
            msg = exc.response.get("Error", {}).get("Message", str(exc))
            logger.error("sagemaker_error", extra={"aws_code": code, "aws_message": msg[:500]})
            if code in ("ValidationError",) and "not found" in msg.lower():
                raise LLMError(f"SageMaker endpoint '{self.endpoint}' not found. Is it deployed and InService?")
            if code == "AccessDeniedException":
                raise LLMError("Access denied calling SageMaker. Check the EC2 instance role policy.")
            raise LLMError(f"SageMaker error ({code})", details=msg[:500])
        except BotoCoreError as exc:
            raise LLMError("Could not reach SageMaker", details=str(exc))

        try:
            return parse_chat_completion(payload)
        except ValueError as exc:
            raise LLMError("Unexpected response from SageMaker endpoint", details=str(exc))
