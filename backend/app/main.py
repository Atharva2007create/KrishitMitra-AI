import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import RequestResponseEndpoint

from app.api.v1.router import router as api_v1_router
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.settings import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    yield


settings = get_settings()
logger = logging.getLogger(__name__)
app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Request-ID"],
)
register_exception_handlers(app)
app.include_router(api_v1_router, prefix=f"/api/{settings.api_version}")


@app.middleware("http")
async def request_observability(request: Request, call_next: RequestResponseEndpoint) -> Response:
    request_id = str(uuid4())
    started = perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "latency_ms": round((perf_counter() - started) * 1000, 2),
        },
    )
    return response


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
