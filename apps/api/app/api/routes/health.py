from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db.redis import get_redis_client
from app.schemas import DependencyHealth, HealthStatus, ReadinessStatus

router = APIRouter()


async def get_redis() -> Redis:
    return get_redis_client()


@router.get("/health", response_model=HealthStatus)
async def health():
    return HealthStatus(status="ok")


@router.get("/health/ready", response_model=ReadinessStatus)
async def readiness(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    checks: dict[str, DependencyHealth] = {}
    overall_status = "ok"

    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = DependencyHealth(status="ok")
    except Exception:
        overall_status = "degraded"
        checks["database"] = DependencyHealth(status="error", detail="unavailable")

    try:
        await redis.ping()
        checks["redis"] = DependencyHealth(status="ok")
    except Exception:
        overall_status = "degraded"
        checks["redis"] = DependencyHealth(status="error", detail="unavailable")

    payload = ReadinessStatus(status=overall_status, checks=checks)
    if overall_status != "ok":
        return JSONResponse(status_code=503, content=payload.model_dump())
    return payload
