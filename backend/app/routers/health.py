from fastapi import APIRouter, Depends

from ..config import Settings, get_settings
from ..services.llm.base import LLMClient
from .common import get_llm, ok

router = APIRouter(tags=["health"])


@router.get("/health")
def health(settings: Settings = Depends(get_settings), llm: LLMClient = Depends(get_llm)):
    """Liveness check used by Docker's healthcheck and the UI header badge. No auth."""
    return ok({"status": "ok", "environment": settings.environment, "provider": llm.provider, "model": llm.model})
