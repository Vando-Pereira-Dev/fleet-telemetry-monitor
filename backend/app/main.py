from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from app.api.routes.telemetry import router as telemetry_router
from app.config import get_settings
from app.db import models  # noqa: F401 — register ORM mappers
from app.db.session import AsyncSessionLocal, engine

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(telemetry_router)


@app.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    """Liveness probe (no database)."""
    return {"status": "ok"}


@app.get("/ready", tags=["ops"])
async def ready() -> dict[str, str]:
    """Readiness: verifies PostgreSQL connectivity."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — surface any driver/connect failure
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"status": "ready", "database": "connected"}


@app.get("/", tags=["ops"])
async def root() -> dict[str, str]:
    return {"service": settings.app_name, "docs": "/docs"}
