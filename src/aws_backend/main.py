from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import (
    community,
    deprecated,
    dtag,
    evidence,
    explore,
    forecast,
    interactions,
    interest,
    kernel,
    managed_agents,
    onc,
    promotion,
    read,
    reports,
    review_dossier,
    journal,
    partner,
    sighting_assist,
    timeseries,
    write,
)
from .state import run_ingestion, storage

if TYPE_CHECKING:
    from fastapi import FastAPI as FastAPIType


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not storage.list_sightings(limit=1):
        run_ingestion(include_live=False)
    try:
        from .exploration.migrate import run_pending_migrations

        run_pending_migrations()
    except Exception:
        pass
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="orcast API",
        description="AWS-native ORCAST sightings, hotspot probability, and report service",
        version="1.0.0",
        lifespan=lifespan,
    )

    # A wildcard origin cannot be combined with credentials (the browser rejects
    # it, and it is unsafe). Only allow credentials when origins are explicit.
    cors_origins = settings.cors_origins
    allow_credentials = cors_origins != ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(read.router)
    app.include_router(write.router)
    app.include_router(community.router)
    app.include_router(forecast.router)
    app.include_router(kernel.router)
    app.include_router(promotion.router)
    app.include_router(review_dossier.router)
    app.include_router(journal.router)
    app.include_router(evidence.router)
    app.include_router(partner.router)
    app.include_router(sighting_assist.router)
    app.include_router(explore.router)
    app.include_router(managed_agents.router)
    app.include_router(interactions.router)
    app.include_router(onc.router)
    app.include_router(reports.router)
    app.include_router(timeseries.router)
    app.include_router(deprecated.router)
    app.include_router(dtag.router)
    app.include_router(interest.router)

    return app


app = create_app()

# Re-export for tests and scripts
from .state import run_ingestion  # noqa: E402, F401
