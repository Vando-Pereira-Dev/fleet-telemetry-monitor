from fastapi import FastAPI

from app.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")


@app.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    """Liveness/readiness probe; does not check DB (added in a later step)."""
    return {"status": "ok"}


@app.get("/", tags=["ops"])
async def root() -> dict[str, str]:
    return {"service": settings.app_name, "docs": "/docs"}
