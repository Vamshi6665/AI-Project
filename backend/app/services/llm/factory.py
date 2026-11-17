from ...config import Settings
from .base import LLMClient


def build_llm_client(settings: Settings) -> LLMClient:
    """Pick the provider once at startup (imports are lazy so mock mode needs no AWS/OpenAI libs)."""
    if settings.llm_provider == "sagemaker":
        from .sagemaker_client import SageMakerClient
        return SageMakerClient(settings)
    if settings.llm_provider == "bedrock":
        from .bedrock_client import BedrockClient
        return BedrockClient(settings)
    if settings.llm_provider == "openai":
        from .openai_client import OpenAIClient
        return OpenAIClient(settings)
    from .mock_client import MockClient
    return MockClient()
