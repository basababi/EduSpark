from pydantic import BaseModel


class HealthStatus(BaseModel):
    status: str


class DependencyHealth(BaseModel):
    status: str
    detail: str | None = None


class ReadinessStatus(BaseModel):
    status: str
    checks: dict[str, DependencyHealth]
