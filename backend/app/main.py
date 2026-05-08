"""FastAPI app assembly + middleware + global exception handlers."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware

from app.config import settings
from app.errors import PrismException, error_response
from app.logging_config import configure_logging, logger
from app.routes import account, auth, chat, health, messages, models, oauth, usage

# Configure logging at module import (uvicorn imports this once).
configure_logging()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    logger.info("prism_starting", host=settings.host, port=settings.port)

    # v0.3: chain monitors + capacity-alert loop run as background tasks.
    # Both are no-ops if disabled via settings.
    chain_tasks: list[asyncio.Task] = []
    capacity_task: asyncio.Task | None = None
    try:
        from app.payments.monitor import cancel_tasks, start_all_monitors
        chain_tasks = await start_all_monitors()
    except Exception as exc:
        logger.error("chain_monitors_start_failed", error=str(exc))

    try:
        from app.monitoring.capacity import start_capacity_loop
        capacity_task = await start_capacity_loop()
    except Exception as exc:
        logger.error("capacity_loop_start_failed", error=str(exc))

    try:
        yield
    finally:
        if capacity_task is not None:
            capacity_task.cancel()
            try:
                await capacity_task
            except (asyncio.CancelledError, Exception):
                pass
        if chain_tasks:
            await cancel_tasks(chain_tasks)
        logger.info("prism_shutdown")


app = FastAPI(
    title="Prism Gateway",
    version="0.1.0",
    description="Transparent AI gateway. cost = price. 0% markup.",
    docs_url="/docs" if settings.debug else None,
    redoc_url=None,
    lifespan=lifespan,
)

# CORS: open by default for v0.1 — clients hit our API from anywhere.
# Adjust if browser-side keys become a concern.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Global exception handlers ----------------------------------------------


@app.exception_handler(PrismException)
async def handle_prism_exception(_request: Request, exc: PrismException):
    logger.warning(
        "prism_exception",
        type=exc.error_type,
        code=exc.code,
        status=exc.status_code,
        message=exc.message,
    )
    return error_response(exc.status_code, exc.message, exc.error_type, exc.code, exc.param)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_request: Request, exc: RequestValidationError):
    return error_response(
        400,
        f"Request validation failed: {exc.errors()}",
        "invalid_request_error",
    )


# ---- Routes -----------------------------------------------------------------

app.include_router(health.router)
app.include_router(models.router)
app.include_router(messages.router)
app.include_router(chat.router)
app.include_router(auth.router)
app.include_router(oauth.router)
app.include_router(account.router)
app.include_router(usage.router)
