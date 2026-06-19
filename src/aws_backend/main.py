from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import community, deprecated, forecast, read, reports, timeseries, write
from .state import run_ingestion, storage

if TYPE_CHECKING:
    from fastapi import FastAPI as FastAPIType


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not storage.list_sightings(limit=1):
        run_ingestion(include_live=False)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="ORCAST AWS Backend",
        description="AWS-native ORCAST sightings, hotspot probability, and report service",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(read.router)
    app.include_router(write.router)
    app.include_router(community.router)
    app.include_router(forecast.router)
    app.include_router(reports.router)
    app.include_router(timeseries.router)
    app.include_router(deprecated.router)

    return app


app = create_app()

# Re-export for tests and scripts
from .state import run_ingestion  # noqa: E402, F401
