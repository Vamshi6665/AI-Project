from fastapi import Request
from fastapi.encoders import jsonable_encoder

from ..logging_config import request_id_var
from ..services.llm.base import LLMClient
from ..services.store import ExtractionStore


def ok(data) -> dict:
    """Success envelope: {"success": true, "data": ..., "request_id": "..."}"""
    return {"success": True, "data": jsonable_encoder(data), "request_id": request_id_var.get()}


def get_llm(request: Request) -> LLMClient:
    return request.app.state.llm


def get_store(request: Request) -> ExtractionStore:
    return request.app.state.store
