"""FastAPI entry point. Run locally:  uvicorn app.main:app --reload --port 8000
Swagger UI: http://localhost:8000/api/docs
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings, production_problems
from .errors import register_exception_handlers
from .logging_config import setup_logging
from .middleware import RequestContextMiddleware
from .routers import auth, extract, health
from .services.llm.factory import build_llm_client
from .services.store import ExtractionStore

logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    problems = production_problems(settings)
    if problems:
        raise RuntimeError("Refusing to start in prod: " + "; ".join(problems))
    app.state.llm = build_llm_client(settings)
    app.state.store = ExtractionStore()
    logger.info("startup", extra={"provider": app.state.llm.provider, "model": app.state.llm.model,
                                  "environment": settings.environment})
    yield
    logger.info("shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app)
    for router in (health.router, auth.router, extract.router):
        app.include_router(router, prefix="/api")
    return app


app = create_app()
