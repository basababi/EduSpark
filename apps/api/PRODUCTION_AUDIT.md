# EduSpark Production-Readiness Audit & Improvement Plan

**Date:** 2026-06-03  
**Status:** CRITICAL gaps identified in security, observability, deployment  
**Estimated effort:** 60-80 engineering hours to production-ready  

---

## SECTION 1: SECURITY HARDENING (CRITICAL)

### 1.1 JWT Strategy: Access Token Blacklist for Logout

**Risk:** Access tokens stored in localStorage can be replayed if leaked until expiry (30 min default). Logout does not immediately invalidate access tokens—only refresh tokens are revoked.  
**Severity:** HIGH  
**Current State:** Refresh token revocation works; access token revocation missing.

**Fix:** Implement access token blacklist in Redis for immediate logout.

**File: `apps/api/app/core/token_blacklist.py` (NEW)**

```python
from datetime import datetime, timezone
from app.db.redis import get_redis_client
from app.core.security import decode_token_claims, TokenValidationError

BLACKLIST_PREFIX = "auth:blacklist:access"

async def blacklist_access_token(token: str) -> None:
    """Blacklist an access token on logout (immediate revocation)."""
    try:
        claims = decode_token_claims(token, expected_type="access")
    except TokenValidationError:
        return  # Already invalid; ignore
    
    redis = get_redis_client()
    key = f"{BLACKLIST_PREFIX}:{claims.jti or claims.sub}"
    ttl = int((datetime.fromtimestamp(claims.exp, tz=timezone.utc) - datetime.now(timezone.utc)).total_seconds())
    ttl = max(ttl, 1)
    await redis.set(key, "1", ex=ttl)

async def is_access_token_blacklisted(token: str) -> bool:
    """Check if an access token has been blacklisted."""
    try:
        claims = decode_token_claims(token, expected_type="access")
    except TokenValidationError:
        return False
    
    redis = get_redis_client()
    key = f"{BLACKLIST_PREFIX}:{claims.jti or claims.sub}"
    exists = await redis.exists(key)
    return exists > 0
```

**Update: `apps/api/app/core/security.py`** (line 119, modify `verify_token`)

```python
async def verify_token_async(token: str, check_blacklist: bool = False) -> str | None:
    """Verify access token and optionally check blacklist."""
    try:
        claims = decode_token_claims(token, expected_type="access")
        if check_blacklist:
            from app.core.token_blacklist import is_access_token_blacklisted
            if await is_access_token_blacklisted(token):
                return None
        return claims.sub
    except TokenValidationError:
        return None
```

**Update: `apps/api/app/api/deps.py`** (modify `get_current_user`)

```python
async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    session: AsyncSession = Depends(get_db)
) -> User:
    from app.core.security import verify_token_async
    from app.core.token_blacklist import is_access_token_blacklisted
    
    # Check blacklist first (fast Redis lookup)
    if await is_access_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
    
    sub = await verify_token_async(token, check_blacklist=False)
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    stmt = (
        select(User)
        .options(selectinload(User.profile), selectinload(User.role))
        .where(User.id == sub)
    )
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user
```

**Update: `apps/api/app/api/routes/auth.py`** (modify `/logout` endpoint)

```python
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    token: str = Depends(oauth2_scheme),
    payload: LogoutRequest | None = Body(default=None),
    query_token: str | None = Query(default=None),
):
    from app.core.token_blacklist import blacklist_access_token
    
    refresh_token = _resolve_refresh_token(payload, query_token)
    
    # Revoke both access and refresh tokens
    await blacklist_access_token(token)
    try:
        await revoke_refresh_token(refresh_token)
    except AuthSessionError:
        pass  # Refresh token already expired/revoked is OK
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

---

### 1.2 Strict Production CORS & Hostname Validation

**Risk:** Current config allows wildcard CORS in development; prod must be explicit.  
**Severity:** MEDIUM

**Update: `apps/api/app/core/config.py`** (add validation)

```python
@model_validator(mode="after")
def validate_cors_in_production(self) -> "Settings":
    if self.environment == "production":
        origins = self.allowed_origins_list
        if "*" in origins or any(o.startswith("*") for o in origins):
            raise ValueError("Wildcard CORS not allowed in production")
        if not all(o.startswith(("https://", "https://")) for o in origins):
            raise ValueError("All origins must be HTTPS in production")
    return self
```

**Update: `apps/api/app/main.py`** (add trusted hosts validation)

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

def get_app() -> FastAPI:
    app = FastAPI(title=settings.project_name, lifespan=lifespan)
    
    # Trusted host middleware (before CORS)
    if settings.environment == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_origins_list,
        )
    
    # CORS after trusted hosts
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # ... rest of app setup
```

---

### 1.3 Per-User Rate Limiting (Sliding Window)

**Risk:** No rate limits; exam season spike can be exploited for DoS or brute-force auth attacks.  
**Severity:** HIGH

**File: `apps/api/app/core/rate_limit.py` (NEW)**

```python
from datetime import datetime, timedelta, timezone
from app.db.redis import get_redis_client

async def check_rate_limit(user_id: str, limit: int = 100, window_seconds: int = 60) -> tuple[bool, int]:
    """Sliding window rate limit. Returns (allowed, remaining)."""
    redis = get_redis_client()
    key = f"ratelimit:{user_id}"
    now = datetime.now(timezone.utc).timestamp()
    window_start = now - window_seconds
    
    # Remove old entries outside window
    await redis.zremrangebyscore(key, 0, window_start)
    
    # Count requests in window
    count = await redis.zcard(key)
    
    if count >= limit:
        return False, 0
    
    # Add current request
    await redis.zadd(key, {str(now): now})
    await redis.expire(key, window_seconds + 10)
    
    return True, limit - count - 1
```

**File: `apps/api/app/api/deps.py` (add rate limit dependency)**

```python
from app.core.rate_limit import check_rate_limit
from fastapi import HTTPException

async def rate_limit_check(user: User = Depends(get_current_user)):
    """Dependency that enforces per-user rate limit."""
    allowed, remaining = await check_rate_limit(
        user.id,
        limit=1000,  # 1000 requests per minute per user
        window_seconds=60,
    )
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": "60"},
        )
    return user
```

**Use in protected routes:**

```python
@router.get("/subjects")
async def read_subjects(
    _: User = Depends(rate_limit_check),  # Rate limit first
    db: AsyncSession = Depends(get_db),
):
    # ... route logic
```

---

### 1.4 Input Validation: Top 3 Vulnerable Routes

**Risk:** Over-posting in quiz attempt, user profile update, and quiz filtering endpoints.  
**Severity:** HIGH

**Fix 1: Quiz attempt over-posting** — `apps/api/app/schemas.py`

```python
from pydantic import BaseModel, Field, field_validator

class QuizAnswerSubmit(BaseModel):
    question_id: str = Field(..., min_length=1, max_length=36)
    selected_answer: str = Field(..., min_length=1, max_length=10)
    
    @field_validator("selected_answer")
    @classmethod
    def validate_answer_format(cls, v: str) -> str:
        # Only allow alphanumeric + _ - 
        if not all(c.isalnum() or c in '_-' for c in v):
            raise ValueError("Invalid answer format")
        return v.strip()

class QuizAttemptSubmitRequest(BaseModel):
    answers: list[QuizAnswerSubmit] = Field(..., max_items=500)
    
    @field_validator("answers")
    @classmethod
    def validate_no_duplicates(cls, v: list) -> list:
        question_ids = [a.question_id for a in v]
        if len(question_ids) != len(set(question_ids)):
            raise ValueError("Duplicate question answers not allowed")
        return v
```

**Fix 2: User profile update** — `apps/api/app/schemas.py`

```python
class UserProfileUpdate(BaseModel):
    """Only allow whitelisted fields for profile updates."""
    full_name: str | None = Field(None, max_length=120)
    locale: str | None = Field(None, pattern="^[a-z]{2}$")  # ISO 639-1
    timezone: str | None = Field(None, max_length=50)
    dark_mode: bool = False
    compact_view: bool = False
    
    class Config:
        # Forbid extra fields (over-posting protection)
        extra = "forbid"
```

**Fix 3: Quiz filtering** — `apps/api/app/api/routes/quizzes.py`

```python
from pydantic import Field

@router.get("")
async def read_quizzes(
    subject_id: str | None = Query(None, min_length=1, max_length=36, regex="^[a-f0-9-]{36}$"),
    topic_id: str | None = Query(None, min_length=1, max_length=36, regex="^[a-f0-9-]{36}$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0, le=10000),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await list_quizzes(db, user, subject_id=subject_id, topic_id=topic_id, limit=limit, offset=offset)
```

---

### 1.5 Secrets Management Checklist

**Production Secrets Rotation:**

1. **JWT_SECRET** (required)
   - Must be ≥32 bytes, cryptographically random
   - Generate: `openssl rand -hex 32`
   - Never commit to git; store in GitHub Secrets or CI/CD vault
   - Rotation: Issue new secret, update all clients within 1 hour, old secret still valid for 30 min refresh window

2. **DATABASE_URL** (required)
   - Format: `postgresql+asyncpg://user:password@host:5432/dbname`
   - Password chars must be URL-encoded (e.g., `@` → `%40`)
   - Never use `localhost` in prod; use managed database endpoint with SSL enforced

3. **REDIS_URL** (required)
   - Format: `redis://:password@host:6379/0`
   - Use TLS in production: `rediss://...`
   - ACLs: Create read-only user for app, restrict to specific keys/commands

4. **.env file template** — `apps/api/.env.example`

```bash
# ENVIRONMENT
ENVIRONMENT=production

# DATABASE
DATABASE_URL=postgresql+asyncpg://eduspark:CHANGE_ME@db.example.com:5432/eduspark_prod

# REDIS
REDIS_URL=rediss://:CHANGE_ME@redis.example.com:6379/0

# JWT
JWT_SECRET=CHANGE_ME_TO_STRONG_32_BYTE_HEX
JWT_EXPIRES_MIN=30
REFRESH_EXPIRES_MIN=43200

# CORS
ALLOWED_ORIGINS=https://app.eduspark.mn,https://www.eduspark.mn

# LOGGING
LOG_LEVEL=INFO

# AI (Optional)
OPENAI_API_KEY=sk-CHANGE_ME
```

---

## SECTION 2: OBSERVABILITY (CRITICAL)

### 2.1 Structured JSON Logging with Request IDs

**File: `apps/api/app/core/logging.py` (NEW)**

```python
import json
import logging
import uuid
from contextvars import ContextVar
from typing import Any

from loguru import logger
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

REQUEST_ID_CONTEXT: ContextVar[str] = ContextVar("request_id", default="")

def setup_logging(environment: str, log_level: str = "INFO"):
    """Configure loguru for JSON output."""
    logger.remove()  # Remove default handler
    
    # JSON handler
    handler_config = {
        "sink": lambda msg: print(msg, end=""),
        "format": json_formatter,
        "level": log_level,
        "serialize": False,  # We format manually
    }
    
    logger.add(handler_config["sink"], format=handler_config["format"], level=handler_config["level"])
    
    if environment == "development":
        # Pretty print for dev
        logger.add(
            lambda msg: print(msg, end=""),
            format="<level>{level: <8}</level> | {name}:{function}:{line} - {message}",
            level="DEBUG",
        )

def json_formatter(record: dict) -> str:
    """Format log record as JSON."""
    log_entry = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "logger": record["name"],
        "message": record["message"],
        "request_id": REQUEST_ID_CONTEXT.get() or "N/A",
        "function": record["function"],
        "line": record["line"],
    }
    
    # Add exception info if present
    if record["exception"]:
        log_entry["exception"] = record["exc_info"]
    
    # Add extra context if present
    if record["extra"]:
        log_entry.update(record["extra"])
    
    return json.dumps(log_entry) + "\n"

class RequestIdMiddleware(BaseHTTPMiddleware):
    """Inject request_id into all requests and logs."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        REQUEST_ID_CONTEXT.set(request_id)
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        logger.info(
            "http_request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "client": request.client.host if request.client else "unknown",
            }
        )
        return response
```

**Update: `apps/api/app/main.py`**

```python
from app.core.logging import setup_logging, RequestIdMiddleware
from app.core.config import settings

def get_app() -> FastAPI:
    app = FastAPI(title=settings.project_name, lifespan=lifespan)
    
    # Setup logging first
    setup_logging(settings.environment, settings.log_level)
    
    # Add request ID middleware
    app.add_middleware(RequestIdMiddleware)
    
    # ... rest of middleware and routes
```

---

### 2.2 Distributed Tracing (OpenTelemetry)

**Add to `requirements.txt`:**

```
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-exporter-jaeger-thrift==1.21.0
opentelemetry-instrumentation-fastapi==0.42b0
opentelemetry-instrumentation-sqlalchemy==0.42b0
opentelemetry-instrumentation-redis==0.42b0
```

**File: `apps/api/app/core/tracing.py` (NEW)**

```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncEngine

def init_tracing(app_name: str = "eduspark-api"):
    """Initialize OpenTelemetry tracing with Jaeger backend."""
    if settings.environment != "production":
        return
    
    jaeger_exporter = JaegerExporter(
        agent_host_name=settings.jaeger_host,
        agent_port=6831,
    )
    
    trace.set_tracer_provider(TracerProvider())
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )
    
    # Instrument libraries
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine_name="eduspark")
    RedisInstrumentor().instrument()
```

**Add to config (`apps/api/app/core/config.py`):**

```python
jaeger_host: str = Field(default="localhost", validation_alias="JAEGER_HOST")
jaeger_enabled: bool = Field(default=False, validation_alias="JAEGER_ENABLED")
```

**Update `apps/api/app/main.py`:**

```python
from app.core.tracing import init_tracing

def get_app() -> FastAPI:
    app = FastAPI(...)
    init_tracing("eduspark-api")
    # ... rest
```

---

### 2.3 Sentry Integration for Error Tracking

**Add to `requirements.txt`:**

```
sentry-sdk[fastapi]==1.40.0
```

**Update: `apps/api/app/main.py`**

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from app.core.config import settings

if settings.environment == "production" and settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[
            FastApiIntegration(),
            RedisIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,
        environment=settings.environment,
        release=settings.app_version or "unknown",
    )
```

**Add to config:**

```python
sentry_dsn: str | None = Field(default=None, validation_alias="SENTRY_DSN")
app_version: str = Field(default="0.1.0", validation_alias="APP_VERSION")
```

---

### 2.4 Enhanced Health Check Endpoint

**Update: `apps/api/app/api/routes/health.py` (NEW)**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime, timezone
from app.api.deps import get_db
from app.db.redis import get_redis_client
from app.db.session import engine
import asyncio

router = APIRouter(prefix="/health", tags=["health"])

class HealthStatus(BaseModel):
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: datetime
    services: dict[str, dict]

@router.get("", response_model=HealthStatus)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Comprehensive health check for all dependencies."""
    timestamp = datetime.now(timezone.utc)
    services = {}
    
    # PostgreSQL check
    try:
        await db.execute("SELECT 1")
        services["postgresql"] = {"status": "healthy", "latency_ms": 5}
    except Exception as e:
        services["postgresql"] = {"status": "unhealthy", "error": str(e)}
    
    # Redis check
    try:
        redis = get_redis_client()
        await redis.ping()
        services["redis"] = {"status": "healthy"}
    except Exception as e:
        services["redis"] = {"status": "unhealthy", "error": str(e)}
    
    # Celery worker check (optional)
    try:
        # Ping a worker with short timeout
        from celery import current_app
        result = current_app.control.inspect().active(timeout=1)
        services["celery"] = {
            "status": "healthy" if result else "degraded",
            "active_workers": len(result) if result else 0,
        }
    except Exception as e:
        services["celery"] = {"status": "unhealthy", "error": str(e)}
    
    # Determine overall status
    statuses = [s.get("status") for s in services.values()]
    if all(s == "healthy" for s in statuses):
        overall_status = "healthy"
    elif any(s == "unhealthy" for s in statuses):
        overall_status = "unhealthy"
    else:
        overall_status = "degraded"
    
    return HealthStatus(
        status=overall_status,
        timestamp=timestamp,
        services=services,
    )
```

---

## SECTION 3: DEPLOYMENT & CI/CD (HIGH)

### 3.1 Production-Ready Dockerfile

**File: `apps/api/Dockerfile.prod` (NEW)**

```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random

COPY --chown=appuser:appuser . .

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

---

### 3.2 Docker Compose (Dev & Prod)

**File: `docker-compose.yml` (development)**

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: eduspark
      POSTGRES_PASSWORD: devpassword
      POSTGRES_DB: eduspark_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U eduspark"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    environment:
      ENVIRONMENT: development
      DATABASE_URL: postgresql+asyncpg://eduspark:devpassword@postgres:5432/eduspark_dev
      REDIS_URL: redis://redis:6379/0
      JWT_SECRET: dev-secret-change-in-production-32-bytes
      ALLOWED_ORIGINS: http://localhost:3000,http://localhost:3001
      LOG_LEVEL: DEBUG
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./apps/api:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  celery_worker:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    environment:
      ENVIRONMENT: development
      DATABASE_URL: postgresql+asyncpg://eduspark:devpassword@postgres:5432/eduspark_dev
      REDIS_URL: redis://redis:6379/0
      JWT_SECRET: dev-secret-change-in-production-32-bytes
    depends_on:
      - postgres
      - redis
    volumes:
      - ./apps/api:/app
    command: celery -A app.celery_app worker --loglevel=info

  celery_beat:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    environment:
      ENVIRONMENT: development
      DATABASE_URL: postgresql+asyncpg://eduspark:devpassword@postgres:5432/eduspark_dev
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - ./apps/api:/app
    command: celery -A app.celery_app beat --loglevel=info

volumes:
  postgres_data:
```

**File: `docker-compose.prod.yml` (production override)**

```yaml
version: "3.9"

services:
  api:
    image: eduspark-api:latest
    environment:
      ENVIRONMENT: production
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      JWT_SECRET: ${JWT_SECRET}
      ALLOWED_ORIGINS: ${ALLOWED_ORIGINS}
      SENTRY_DSN: ${SENTRY_DSN}
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: "1"
          memory: 512M
        reservations:
          cpus: "0.5"
          memory: 256M

  celery_worker:
    image: eduspark-api:latest
    environment:
      ENVIRONMENT: production
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      JWT_SECRET: ${JWT_SECRET}
    restart: always
    command: celery -A app.celery_app worker --concurrency=4 --loglevel=info
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: "1"
          memory: 512M
```

---

### 3.3 GitHub Actions CI/CD Pipeline

**File: `.github/workflows/deploy.yml` (NEW)**

```yaml
name: Deploy

on:
  push:
    branches: [main, staging]
    paths:
      - "apps/api/**"
      - ".github/workflows/deploy.yml"

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}/eduspark-api

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
          cache: "pip"
      
      - run: pip install -r apps/api/requirements.txt
      
      - run: |
          cd apps/api
          python -m pytest tests/ --cov=app --cov-report=xml
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test
          REDIS_URL: redis://localhost:6379/0
          JWT_SECRET: test-secret-32-bytes-long-1234567890ab
      
      - uses: codecov/codecov-action@v3
        with:
          files: ./apps/api/coverage.xml

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
          cache: "pip"
      
      - run: |
          pip install ruff black mypy
          cd apps/api
          ruff check .
          black --check .
          mypy app/

  build-and-push:
    needs: [test, lint]
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4
      
      - uses: docker/setup-buildx-action@v2
      
      - uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - uses: docker/build-push-action@v4
        with:
          context: ./apps/api
          file: ./apps/api/Dockerfile.prod
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache
          cache-to: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache,mode=max

  deploy:
    needs: build-and-push
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to production
        run: |
          # Example using Railway/Render webhook
          curl -X POST ${{ secrets.DEPLOY_WEBHOOK }} \
            -H "Authorization: Bearer ${{ secrets.DEPLOY_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d '{"image":"${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}"}'
```

---

### 3.4 Infrastructure Recommendation

**Comparison for <1,000 daily users in Mongolia:**

| Platform | Cost/mo | PostgreSQL | Redis | Auto-scale | CDN | Notes |
|----------|---------|-----------|-------|-----------|-----|-------|
| **Railway** | ~$50-100 | ✅ Managed | ✅ Managed | ✅ Yes | Via Cloudflare | **RECOMMENDED** — Best for Mongolia, simple deployments |
| Render | ~$50-100 | ✅ Managed | ❌ Need add-on | ✅ Yes | Via Cloudflare | Good but slower TLS renewal |
| Fly.io | ~$50-80 | ✅ Managed | ✅ Managed | ✅ Yes | ✅ Built-in | Geographic placement options; more complex |
| VPS (Linode) | ~$30-50 | ❌ Self-managed | ❌ Self-managed | ❌ Manual | Need separate | Cheapest but high ops burden |

**Recommendation: Railway**
- Simplest deployment workflow (git push → deploy)
- PostgreSQL + Redis both managed & backed up
- Good performance from Singapore region (close to Mongolia)
- Automatic SSL, environment secrets, PR deployments
- Cost: ~$75/month for production setup

**Setup Steps:**
1. Create Railway project: https://railway.app
2. Connect GitHub repo
3. Set environment variables in Railway dashboard (DATABASE_URL, REDIS_URL, JWT_SECRET, etc.)
4. Deploy via `git push main`
5. Monitor via Railway dashboard

---

### 3.5 Frontend Deployment Fix

**Problem:** gh-pages unsuitable for authenticated routes (static site, no backend).

**Solution: Use Vercel for Next.js**

**File: `vercel.json` (NEW)**

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "env": {
    "NEXT_PUBLIC_API_URL": "@next_public_api_url"
  },
  "functions": {
    "api/**": {
      "memory": 1024,
      "maxDuration": 60
    }
  },
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "${NEXT_PUBLIC_API_URL}/api/:path*"
    }
  ]
}
```

**Update: `apps/web/.env.production`**

```bash
NEXT_PUBLIC_API_URL=https://api.eduspark.mn
```

**Deploy:** Push to GitHub → Vercel auto-deploys

---

### 3.6 Alembic Migration Strategy

**Safe migration workflow:**

1. **Before deploy:** Run migrations in a transaction
2. **Backward-compatible migrations:** Add column → Deploy code → Drop old column in next release
3. **Rollback:** Keep previous migration scripts; revert with `alembic downgrade -1`

**File: `apps/api/alembic/env.py` (add transaction safety)**

```python
def run_migrations_online() -> None:
    """Run migrations with transaction support."""
    configuration = config.get_section(config.config_ini_section)
    
    with connectable.begin() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Enable transactional DDL
            transaction_per_migration=True,
        )
        
        with context.begin_transaction():
            context.run_migrations()
```

**CI deployment flow:**

```bash
# In deploy script
docker run --rm -e DATABASE_URL=$DATABASE_URL eduspark-api:latest \
  alembic upgrade head

# If fails, Kubernetes/Docker auto-rollback to previous version
```

---

## SECTION 4: DATABASE OPTIMIZATION (HIGH)

### 4.1 Critical Indexes

**File: `apps/api/alembic/versions/XXXX_add_indexes.py` (NEW)**

```python
from sqlalchemy import text

def upgrade():
    """Add production-critical indexes."""
    op.execute(text("CREATE INDEX idx_user_email ON \"user\"(email)"))
    op.execute(text("CREATE INDEX idx_user_is_active ON \"user\"(is_active)"))
    op.execute(text("CREATE INDEX idx_quiz_topic_id ON quiz(topic_id)"))
    op.execute(text("CREATE INDEX idx_quizattempt_user_id_completed ON quizattempt(user_id, completed_at DESC) WHERE completed_at IS NOT NULL"))
    op.execute(text("CREATE INDEX idx_quizanswer_attempt_id ON quizanswer(attempt_id)"))
    op.execute(text("CREATE INDEX idx_quizquestion_quiz_id ON quizquestion(quiz_id)"))
    op.execute(text("CREATE INDEX idx_studysession_user_id ON studysession(user_id)"))
    op.execute(text("CREATE INDEX idx_chatmessage_session_id ON chatmessage(session_id, created_at DESC)"))

def downgrade():
    op.execute(text("DROP INDEX IF EXISTS idx_user_email"))
    op.execute(text("DROP INDEX IF EXISTS idx_user_is_active"))
    # ... drop all
```

---

### 4.2 N+1 Query Fixes

**Issue 1: `get_quiz_attempt_history` (quiz_service.py:297)**

Current: 3 separate queries (attempts, answer_counts, total_questions)  
Fixed: Single query with subqueries

```python
async def get_quiz_attempt_history(
    db: AsyncSession,
    user: User,
    *,
    limit: int = 20,
) -> list[QuizAttemptHistoryItemRead]:
    safe_limit = max(1, min(limit, 100))
    
    # Subquery: correct answer count per attempt
    correct_subq = (
        select(
            QuizAnswer.attempt_id,
            func.sum(case((QuizAnswer.is_correct.is_(True), 1), else_=0)).label("correct_count")
        )
        .group_by(QuizAnswer.attempt_id)
        .subquery()
    )
    
    # Subquery: total questions per quiz
    total_subq = (
        select(
            QuizQuestion.quiz_id,
            func.count(QuizQuestion.id).label("total_questions")
        )
        .group_by(QuizQuestion.quiz_id)
        .subquery()
    )
    
    # Single query with both subqueries
    attempts_stmt = (
        select(
            QuizAttempt.id.label("attempt_id"),
            QuizAttempt.quiz_id,
            QuizAttempt.score,
            QuizAttempt.completed_at,
            Quiz.title.label("quiz_title"),
            Subject.name.label("subject_name"),
            func.coalesce(correct_subq.c.correct_count, 0).label("correct_count"),
            func.coalesce(total_subq.c.total_questions, 0).label("total_questions"),
        )
        .select_from(QuizAttempt)
        .join(Quiz, Quiz.id == QuizAttempt.quiz_id)
        .outerjoin(Topic, Topic.id == Quiz.topic_id)
        .outerjoin(Module, Module.id == Topic.module_id)
        .outerjoin(Subject, Subject.id == Module.subject_id)
        .outerjoin(correct_subq, correct_subq.c.attempt_id == QuizAttempt.id)
        .outerjoin(total_subq, total_subq.c.quiz_id == Quiz.id)
        .where(
            QuizAttempt.user_id == user.id,
            QuizAttempt.completed_at.is_not(None),
        )
        .order_by(QuizAttempt.completed_at.desc())
        .limit(safe_limit)
    )
    
    attempt_rows = (await db.execute(attempts_stmt)).all()
    
    return [
        QuizAttemptHistoryItemRead(
            attempt_id=row.attempt_id,
            quiz_id=row.quiz_id,
            quiz_title=row.quiz_title,
            subject_name=row.subject_name,
            score=_round_score(row.score),
            correct_count=int(row.correct_count),
            total_questions=int(row.total_questions),
            completed_at=row.completed_at,
        )
        for row in attempt_rows
    ]
```

**Issue 2: `get_current_user` in deps.py (line 24)**

Currently loads User + Profile + Role separately; use selectinload.

```python
# Already fixed in current code ✅
stmt = (
    select(User)
    .options(selectinload(User.profile), selectinload(User.role))
    .where(User.id == sub)
)
```

**Issue 3: `list_quizzes` with joined load**

```python
# Add after fetching quizzes
result = await db.execute(
    select(Quiz)
    .options(
        selectinload(Quiz.questions),
        selectinload(Quiz.topic).selectinload(Topic.module).selectinload(Module.subject)
    )
)
```

---

### 4.3 Connection Pooling Config

**Update: `apps/api/app/db/session.py`**

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    poolclass=QueuePool,
    pool_size=20,  # Number of connections to maintain
    max_overflow=40,  # Allow up to 40 additional connections
    pool_recycle=3600,  # Recycle connections after 1 hour (RDS timeout)
    pool_pre_ping=True,  # Test connections before use
    connect_args={
        "timeout": 10,  # Connection timeout
        "command_timeout": 60,  # Query timeout
    },
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)
```

**PgBouncer config** (`pgbouncer.ini` on app server):

```ini
[databases]
eduspark = host=db.example.com port=5432 dbname=eduspark

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 10
reserve_pool_size = 5
reserve_pool_timeout = 3
max_db_connections = 100
```

---

### 4.4 Redis Caching Strategy

**File: `apps/api/app/core/cache.py` (NEW)**

```python
from datetime import timedelta
from functools import wraps
import json
from typing import Any, Callable, TypeVar
from app.db.redis import get_redis_client

T = TypeVar("T")

async def cache_aside(
    key: str,
    ttl: int = 300,
    fetch_func: Callable[[], Any] | None = None,
) -> Any | None:
    """Cache-aside pattern: check cache, fall through to fetch_func if miss."""
    redis = get_redis_client()
    
    # Check cache
    cached = await redis.get(key)
    if cached:
        return json.loads(cached)
    
    # Cache miss; fetch
    if fetch_func is None:
        return None
    
    value = await fetch_func()
    if value is not None:
        await redis.setex(key, ttl, json.dumps(value, default=str))
    
    return value

# Cache invalidation patterns
async def invalidate_user_cache(user_id: str):
    """Invalidate all user-specific caches on profile update."""
    redis = get_redis_client()
    pattern = f"user:{user_id}:*"
    keys = await redis.keys(pattern)
    if keys:
        await redis.delete(*keys)

async def invalidate_quiz_cache(quiz_id: str):
    """Invalidate quiz caches on content change."""
    redis = get_redis_client()
    keys = [
        f"quiz:{quiz_id}:detail",
        f"quiz:{quiz_id}:questions",
    ]
    await redis.delete(*keys)
```

**Cache-eligible queries:**

1. **Lesson content** (TTL: 1 hour) — rarely changes during day
2. **User progress** (TTL: 5 min) — check quiz score, update hourly
3. **Leaderboard** (TTL: 30 min) — recompute periodically

---

### 4.5 Backup Strategy

**File: `scripts/backup.sh` (NEW)**

```bash
#!/bin/bash
set -e

# Configuration
DB_HOST=${DATABASE_HOST:-db.example.com}
DB_USER=${DATABASE_USER:-eduspark}
DB_NAME=${DATABASE_NAME:-eduspark}
BACKUP_DIR=${BACKUP_DIR:-/backups/eduspark}
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Full backup
BACKUP_FILE="$BACKUP_DIR/eduspark_$(date +%Y%m%d_%H%M%S).sql.gz"
pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" | gzip > "$BACKUP_FILE"
echo "✓ Backup created: $BACKUP_FILE ($(du -h $BACKUP_FILE | cut -f1))"

# Verify backup
gunzip -t "$BACKUP_FILE" && echo "✓ Backup verified"

# Clean old backups (keep last 30 days)
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
echo "✓ Cleaned backups older than $RETENTION_DAYS days"

# Upload to S3 (optional)
if command -v aws &> /dev/null; then
    aws s3 cp "$BACKUP_FILE" "s3://eduspark-backups/" --sse AES256
    echo "✓ Backup uploaded to S3"
fi
```

**Cron job (add to production server):**

```bash
# Daily backup at 2 AM UTC
0 2 * * * /opt/eduspark/scripts/backup.sh >> /var/log/eduspark_backup.log 2>&1
```

---

### 4.6 SQLite → PostgreSQL Migration Gotchas

1. **UUID vs String** — PostgreSQL: use `UUID` type; SQLite: stored as string. Use `CAST(uuid_column::text)` for compatibility.
2. **DateTime precision** — PostgreSQL: 6 decimal places; SQLite: seconds only. Alembic handles migration automatically.
3. **JSON types** — SQLite: stored as TEXT; PostgreSQL: native JSON. No code change needed (SQLAlchemy handles).
4. **Auto-increment IDs** — Using UUID (good), but ensure `default=lambda: str(uuid.uuid4())` on all models.
5. **Foreign key constraints** — Enabled by default in PostgreSQL; SQLite requires `PRAGMA foreign_keys=ON`. Already handled in SQLAlchemy.

---

## SECTION 5: AI / LLM INTEGRATION (MEDIUM)

### 5.1 Provider Selection: Claude Recommendation

**Comparison Matrix (for 1,000 students × 20 messages/day = 20k messages/day):**

| Factor | OpenAI GPT-4o | Anthropic Claude 3 | Llama 3 (Ollama) |
|--------|-------|-------|-------|
| **Mongolian quality** | Medium | ✅ **Excellent** | Medium (undertrained) |
| **Cost/1M tokens** | $30 input, $60 output | $3 input, $15 output | Free (self-hosted) |
| **Monthly cost (20k msg)** | ~$150-200 | ~$15-20 | $0 + infra |
| **Latency** | 1-2s | 0.5-1s | 2-5s (depends on GPU) |
| **Hosting** | API only | API + self-hosted | Self-hosted required |
| **Context window** | 128k | 200k | 8k-32k |
| **Mongolian STEM data** | Limited | ✅ Better | Limited |

**Recommendation: Anthropic Claude 3.5 Sonnet**
- Best Mongolian language quality (trained on diverse multilingual data)
- Lowest cost at scale
- Excellent for Socratic tutoring (strong reasoning)
- Streaming API built-in
- Recommended: Pay-per-use API initially, migrate to dedicated tokens if usage >100k/month

---

### 5.2 RAG Pipeline Design

**Architecture:**

```
Lesson Content → Vectorize (OpenAI/Jina) → Store (pgvector) → Query → Claude + Context
```

**Implementation Plan:**

1. **Indexing:** Celery task to chunk lessons and embed
2. **Retrieval:** FastAPI endpoint queries pgvector
3. **Generation:** Claude streams response with retrieved context

**File: `apps/api/app/services/rag_service.py` (NEW)**

```python
import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
import numpy as np
import httpx
from app.core.config import settings
from app.models import Document, DocumentChunk, EmbeddingMetadata

async def create_document_chunks(
    db: AsyncSession,
    lesson_id: str,
    content: str,
    embedding_model: str = "text-embedding-3-small",
) -> list[DocumentChunk]:
    """Chunk lesson content and store with embeddings."""
    # Simple chunking strategy: 500 token chunks
    chunks = [
        content[i:i+2000] for i in range(0, len(content), 2000)
    ]
    
    # Get embeddings from OpenAI
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {settings.openai_api_key.get_secret_value()}"}
        resp = await client.post(
            "https://api.openai.com/v1/embeddings",
            json={
                "model": embedding_model,
                "input": chunks,
            },
            headers=headers,
            timeout=30,
        )
        embeddings_data = resp.json()
    
    # Store chunks and embeddings
    doc_chunks = []
    for i, (chunk_text, emb_data) in enumerate(zip(chunks, embeddings_data["data"])):
        embedding_vector = emb_data["embedding"]
        
        chunk = DocumentChunk(
            document_id=lesson_id,
            sequence_num=i,
            chunk_text=chunk_text,
            embedding=embedding_vector,
            metadata={
                "lesson_id": lesson_id,
                "chunk_index": i,
                "model": embedding_model,
            }
        )
        db.add(chunk)
        doc_chunks.append(chunk)
    
    await db.commit()
    return doc_chunks

async def retrieve_relevant_chunks(
    db: AsyncSession,
    query: str,
    top_k: int = 5,
) -> list[DocumentChunk]:
    """Retrieve top K similar chunks using pgvector similarity search."""
    # Get query embedding
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {settings.openai_api_key.get_secret_value()}"}
        resp = await client.post(
            "https://api.openai.com/v1/embeddings",
            json={
                "model": "text-embedding-3-small",
                "input": [query],
            },
            headers=headers,
            timeout=30,
        )
        query_embedding = resp.json()["data"][0]["embedding"]
    
    # Vector similarity search using pgvector
    # Assumes pgvector extension installed: CREATE EXTENSION vector
    stmt = text("""
        SELECT id, document_id, chunk_text, embedding <-> :embedding AS distance
        FROM documentchunk
        ORDER BY distance
        LIMIT :top_k
    """)
    
    result = await db.execute(
        stmt,
        {"embedding": query_embedding, "top_k": top_k}
    )
    rows = result.fetchall()
    
    chunk_ids = [row[0] for row in rows]
    chunks = await db.execute(
        select(DocumentChunk).where(DocumentChunk.id.in_(chunk_ids))
    )
    return list(chunks.scalars())
```

---

### 5.3 Streaming Chat Endpoint

**File: `apps/api/app/api/routes/chat.py` (NEW)**

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import anthropic
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_db
from app.models import User, ChatSession, ChatMessage
from app.schemas import ChatMessageCreate
from app.services.rag_service import retrieve_relevant_chunks
from datetime import datetime, timezone
import json

router = APIRouter(prefix="/chat", tags=["chat"])
anthropic_client = anthropic.Anthropic()

@router.post("/sessions")
async def create_chat_session(
    db: AsyncSession,
    user: User = Depends(get_current_user),
):
    """Create a new chat session."""
    session = ChatSession(user_id=user.id)
    db.add(session)
    await db.commit()
    return {"session_id": session.id}

@router.post("/sessions/{session_id}/messages")
async def stream_chat_message(
    session_id: str,
    payload: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Stream Claude response with RAG context."""
    # Retrieve relevant lesson chunks
    relevant_chunks = await retrieve_relevant_chunks(
        db,
        payload.content,
        top_k=3,
    )
    
    context = "\n\n".join([
        f"[Source: Lesson {chunk.metadata.get('lesson_id', 'unknown')}]\n{chunk.chunk_text}"
        for chunk in relevant_chunks
    ])
    
    # Build prompt
    system_prompt = """You are an expert Mongolian STEM tutor. Use the provided lesson context 
to answer student questions. Be encouraging, Socratic (ask leading questions), and reference 
lesson content when relevant. Respond in Mongolian."""
    
    # Create user message record (before stream)
    user_msg = ChatMessage(
        session_id=session_id,
        user_id=user.id,
        role="user",
        content=payload.content,
    )
    db.add(user_msg)
    await db.flush()
    
    # Create placeholder assistant message
    assistant_msg = ChatMessage(
        session_id=session_id,
        user_id=user.id,
        role="assistant",
        content="",  # Will be filled during streaming
    )
    db.add(assistant_msg)
    await db.flush()
    
    async def generate_stream():
        full_response = ""
        async with anthropic_client.messages.stream(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=f"{system_prompt}\n\n[LESSON CONTEXT]\n{context}",
            messages=[
                {
                    "role": "user",
                    "content": payload.content,
                }
            ],
        ) as stream:
            async for text in stream.text_stream:
                full_response += text
                yield f"data: {json.dumps({'content': text})}\n\n"
        
        # Save full response after streaming completes
        assistant_msg.content = full_response
        await db.commit()
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
```

---

### 5.4 System Prompt for Mongolian STEM Tutoring

```
You are EduSpark, an expert Mongolian STEM tutor for high school students (grades 10-12).

**Your role:**
- Help students understand complex concepts through Socratic questioning
- Use real-world examples relevant to Mongolian context (mining, herding, weather patterns)
- Adapt explanations based on the student's level (beginner/intermediate/advanced)
- Encourage critical thinking rather than memorization

**Teaching principles:**
1. Ask a guiding question before giving the answer
2. Break complex topics into digestible steps
3. Use diagrams and analogies (e.g., "Like a ger frame..."; "Think of a herding pattern")
4. Validate correct reasoning; gently redirect misconceptions
5. Reference provided lesson content when available

**Mongolian-specific context:**
- Use Mongolian scientific terminology (e.g., "цахилгаан оронц" for electric field)
- Reference Mongolian geography (Gobi, Khangai mountains, lake systems)
- Relate physics to traditional Mongolian practices (lever physics in tools, thermodynamics in gers)
- Be culturally respectful and encouraging

**Language:**
- Respond in Mongolian (Cyrillic script)
- Use formal, educational tone
- Keep sentences clear and concise
- Avoid idioms that don't translate well

**Boundaries:**
- Only discuss STEM subjects (Mathematics, Physics, Chemistry, Biology)
- Politely redirect non-academic questions
- Do not provide homework answers directly; guide the student to the answer
```

---

### 5.5 Cost Controls & Rate Limiting

**File: `apps/api/app/core/llm_budget.py` (NEW)**

```python
from datetime import datetime, timedelta, timezone
from app.db.redis import get_redis_client

BUDGET_PREFIX = "llm:budget"
TOKENS_PER_MESSAGE_EST = 500  # Conservative estimate

async def check_daily_budget(user_id: str, max_messages: int = 20) -> bool:
    """Check if user has exceeded daily message limit."""
    redis = get_redis_client()
    today = datetime.now(timezone.utc).date().isoformat()
    key = f"{BUDGET_PREFIX}:{user_id}:{today}"
    
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 86400)  # 24 hours
    
    return count <= max_messages

async def get_user_budget_remaining(user_id: str) -> int:
    """Get remaining messages for today."""
    redis = get_redis_client()
    today = datetime.now(timezone.utc).date().isoformat()
    key = f"{BUDGET_PREFIX}:{user_id}:{today}"
    
    count = await redis.get(key) or 0
    return max(0, 20 - int(count))

async def log_token_usage(user_id: str, input_tokens: int, output_tokens: int):
    """Track token usage for billing."""
    redis = get_redis_client()
    key = f"tokens:monthly:{user_id}:{datetime.now(timezone.utc).strftime('%Y%m')}"
    await redis.incrby(key, input_tokens + output_tokens)
```

**Add middleware to chat route:**

```python
@router.post("/sessions/{session_id}/messages")
async def stream_chat_message(...):
    budget_ok = await check_daily_budget(user.id, max_messages=20)
    if not budget_ok:
        raise HTTPException(
            status_code=429,
            detail=f"Daily message limit reached. Remaining: {await get_user_budget_remaining(user.id)}",
        )
    # ... rest
```

---

## SECTION 6: PERFORMANCE & SCALING (MEDIUM)

### 6.1 Celery Broker Configuration

**File: `apps/api/app/celery_app.py` (NEW)**

```python
from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery("eduspark")

# Configure Redis as broker and backend
celery_app.conf.update(
    broker_url=settings.redis_url,
    result_backend=settings.redis_url,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    accept_content=["json"],
    task_serializer="json",
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3300,  # 55 min soft limit
)

@celery_app.task(bind=True, max_retries=3)
def example_task(self, user_id: str):
    """Example task with retry logic."""
    try:
        # Do work
        pass
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

**Celery health check:**

```python
from celery.result import AsyncResult

@app.get("/health/celery")
async def celery_health():
    """Check Celery worker availability."""
    try:
        from app.celery_app import celery_app
        result = celery_app.control.inspect().active()
        if result:
            return {"status": "healthy", "workers": len(result)}
        else:
            return {"status": "unhealthy", "error": "No active workers"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

---

### 6.2 Async Blocking Anti-Patterns

**Common mistakes and fixes:**

1. **Blocking DB query in async route:**
```python
# ❌ WRONG
async def get_user(user_id: str):
    user = session.query(User).filter_by(id=user_id).first()  # Blocks event loop!

# ✅ RIGHT
async def get_user(user_id: str, db: AsyncSession):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
```

2. **Sleep instead of async wait:**
```python
# ❌ WRONG
import time
async def delayed_task():
    time.sleep(5)  # Blocks entire worker

# ✅ RIGHT
import asyncio
async def delayed_task():
    await asyncio.sleep(5)
```

3. **Sync requests in async handler:**
```python
# ❌ WRONG
import requests
async def fetch_data():
    response = requests.get("https://api.example.com")  # Blocks!

# ✅ RIGHT
import httpx
async def fetch_data():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com")
```

4. **CPU-bound work on event loop:**
```python
# ❌ WRONG
async def compute():
    result = sum(range(100000000))  # Blocks event loop

# ✅ RIGHT
from concurrent.futures import ThreadPoolExecutor
async def compute():
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, lambda: sum(range(100000000)))
```

5. **Context manager without await:**
```python
# ❌ WRONG
async def save_user(user: User, db: AsyncSession):
    db.add(user)
    db.commit()  # Not awaited!

# ✅ RIGHT
async def save_user(user: User, db: AsyncSession):
    db.add(user)
    await db.commit()
```

**Detection:** Use `ruff` rule:
```bash
ruff check --select=ASYNC app/
```

---

### 6.3 Load Test with Locust

**File: `apps/api/tests/load_test.py` (NEW)**

```python
from locust import HttpUser, task, between, events
from random import choice, randint
import json

class EduSparkUser(HttpUser):
    wait_time = between(2, 5)
    
    def on_start(self):
        """Authenticate before running tasks."""
        resp = self.client.post("/auth/login", json={
            "email": f"user{randint(1, 100)}@example.mn",
            "password": "password123",
        })
        if resp.status_code == 200:
            self.access_token = resp.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.access_token}"}
        else:
            self.headers = {}
    
    @task(10)
    def learning_flow(self):
        """Flow: Fetch subjects → view lesson."""
        # Get subjects
        self.client.get("/subjects", headers=self.headers)
        
        # Get subject detail
        subject_id = choice(["subj-1", "subj-2", "subj-3"])
        resp = self.client.get(f"/subjects/{subject_id}", headers=self.headers)
        
        if resp.status_code == 200:
            # Get a lesson
            lesson_id = "lesson-1"  # Should come from subject response
            self.client.get(f"/lessons/{lesson_id}", headers=self.headers)
    
    @task(5)
    def quiz_flow(self):
        """Flow: Get quizzes → attempt quiz."""
        # List quizzes
        resp = self.client.get("/quizzes", headers=self.headers)
        
        if resp.status_code == 200 and resp.json():
            quiz = resp.json()[0]
            quiz_id = quiz["id"]
            
            # Get quiz detail
            self.client.get(f"/quizzes/{quiz_id}", headers=self.headers)
            
            # Submit attempt (simplified)
            self.client.post(f"/quizzes/{quiz_id}/attempts", 
                json={"answers": []},
                headers=self.headers
            )
    
    @task(3)
    def chat_flow(self):
        """Flow: Create session → send message."""
        # Create session
        resp = self.client.post("/chat/sessions", headers=self.headers)
        if resp.status_code == 200:
            session_id = resp.json()["session_id"]
            
            # Send message
            self.client.post(
                f"/chat/sessions/{session_id}/messages",
                json={"content": "How do I solve quadratic equations?"},
                headers=self.headers,
            )

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("Load test started")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print(f"\nTest completed.")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Failed: {environment.stats.total.num_failures}")
    print(f"Avg response time: {environment.stats.total.avg_response_time:.0f}ms")
    print(f"p95 response time: {environment.stats.total.get_response_time_percentile(0.95):.0f}ms")
```

**Run load test:**

```bash
locust -f tests/load_test.py \
  --host=http://localhost:8000 \
  --users=100 \
  --spawn-rate=10 \
  --run-time=10m \
  --headless
```

**Success criteria:**
- p95 latency: <500ms
- p99 latency: <2000ms
- Error rate: <0.1%

---

### 6.4 CDN Setup (Cloudflare)

**Cloudflare Free Tier for static assets:**

1. **Add domain:** https://dash.cloudflare.com
2. **Configure DNS:** Point `app.eduspark.mn` to Vercel
3. **Cache rules:** 
   - `/api/*` → Don't cache
   - `/_next/static/*` → Cache 1 year
   - `/images/*` → Cache 1 month
   - `/ (HTML)` → Cache 1 hour, but respect Cache-Control header

**Vercel + Cloudflare config:**

```json
{
  "caching": {
    "default": 3600,
    "staticAssets": 31536000,
    "api": 0
  }
}
```

---

### 6.5 Exam Season Scaling Playbook

**1-page runbook for Mongolian exam periods (June, October):**

```
EDUSPARK EXAM SEASON SCALING PLAYBOOK
========================================

Trigger: Traffic projection >5x normal (~100 concurrent users)

PRE-SCALING (Do 24-48 hours before)
1. Review metrics: CPU, DB connections, Redis memory
2. Set up monitoring alerts: CPU >70%, DB pool >80%, Redis >80%
3. Test scaling procedure: Scale to 2 replicas, verify no errors
4. Notify oncall: "Scaling event next 48h"

SCALING SEQUENCE
1. Database:
   - Increase RDS instance size (t3.medium → t3.large)
   - Scale read replicas from 0 → 2 (async)
   - Verify no connection issues for 5 min

2. Redis (same instance, just monitor):
   - Verify memory <50% at peak
   - If needed: t3.medium → cache.r7g.xlarge

3. API (Uvicorn workers):
   - Scale Railway/Render replicas: 1 → 3
   - Monitor first 10 min for errors
   - If p99 latency >2s, scale to 5 replicas

4. Celery workers:
   - Scale workers: 1 → 2
   - Monitor queue depth (target: <100 tasks)

POST-SCALING
1. Monitor for 24h:
   - Error rate should stay <0.1%
   - p99 latency target: <1000ms
   
2. Rollback if problems:
   - Scale down by 50% every 30 min
   - Notify team if p99 latency exceeds 2s

3. Deactivate scaling when traffic drops:
   - Revert to normal config after peak ends
   - Archive metrics for next year
```

---

## MASTER PRIORITY LIST

**Ranked by: (1) Blocks prod, (2) Security/data risk, (3) Performance, (4) DX**

### CRITICAL (Week 1) — Production Blockers

1. **Access token blacklist on logout** (Security: HIGH) — 2 hours
2. **Production-grade CORS + hostname validation** (Security: HIGH) — 1 hour
3. **Production Dockerfile + non-root user** (Security: MEDIUM) — 1.5 hours
4. **Database connection pooling + asyncpg config** (Stability: HIGH) — 2 hours
5. **Celery Redis broker confirmation** (Stability: HIGH) — 0.5 hours
6. **Error tracking (Sentry) integration** (Observability: HIGH) — 2 hours
7. **Health check endpoint** (Monitoring: HIGH) — 1 hour
8. **Alembic safe migrations + CI/CD pipeline** (Deployment: HIGH) — 4 hours

**Subtotal: ~14 hours**

### HIGH (Week 2) — Security + Data Integrity

9. **N+1 query fixes** (Performance: HIGH) — 3 hours
10. **Per-user rate limiting middleware** (Security: MEDIUM) — 1.5 hours
11. **Structured JSON logging + request IDs** (Observability: MEDIUM) — 2 hours
12. **Database indexes (8 critical)** (Performance: HIGH) — 1 hour
13. **Secrets management checklist + rotation procedure** (Security: CRITICAL) — 1 hour
14. **Input validation on top 3 routes** (Security: MEDIUM) — 2 hours
15. **Redis caching strategy (lesson content, progress)** (Performance: MEDIUM) — 2 hours

**Subtotal: ~12.5 hours**

### MEDIUM (Week 3) — Scale & Observability

16. **Infrastructure recommendation + Railway setup** (Operations: MEDIUM) — 2 hours
17. **Frontend deployment (Vercel)** (Deployment: MEDIUM) — 1.5 hours
18. **OpenTelemetry distributed tracing** (Observability: LOW) — 3 hours
19. **LLM provider selection (Claude + RAG)** (Product: MEDIUM) — 2 hours
20. **Streaming chat endpoint** (Feature: MEDIUM) — 4 hours
21. **Locust load test + scaling playbook** (Operations: MEDIUM) — 3 hours
22. **Backup + recovery procedure** (Operations: HIGH) — 1 hour

**Subtotal: ~16.5 hours**

### LOW (Ongoing)

23. **Async code audit + ruff rules** (DX: LOW) — 2 hours
24. **Mongolian STEM tutor prompt engineering** (Product: MEDIUM) — 2 hours
25. **LLM cost controls + rate limiting** (Operations: LOW) — 1 hour
26. **SQLite → PostgreSQL migration tests** (Operations: LOW) — 1 hour

---

## DONE CHECKLIST

### Security Hardening
- [ ] Access token blacklist on logout implemented
- [ ] Refresh token rotation validated
- [ ] CORS whitelist enforced in production
- [ ] Trusted host middleware added
- [ ] Per-user rate limiting dependency created
- [ ] Input validation (over-posting) patterns added to 3 routes
- [ ] Secrets management checklist created
- [ ] JWT_SECRET strength validation in config

### Observability
- [ ] Structured JSON logging with Loguru configured
- [ ] Request ID middleware injecting into all logs
- [ ] OpenTelemetry tracing wired (Jaeger backend)
- [ ] Sentry error tracking integrated
- [ ] Health check endpoint covers PostgreSQL + Redis + Celery
- [ ] Prometheus alert rules defined (p99 latency, error rate, pool exhaustion, queue depth, failed logins)

### Deployment
- [ ] Multi-stage production Dockerfile (non-root user, health check)
- [ ] docker-compose.yml for local dev with all services
- [ ] docker-compose.prod.yml overrides
- [ ] GitHub Actions CI/CD pipeline (test → lint → build → push → deploy)
- [ ] Environment secrets management via GitHub Secrets
- [ ] Railway setup and deployment (PostgreSQL + Redis managed)
- [ ] Vercel setup for Next.js frontend
- [ ] Alembic migration strategy documented + transactional DDL enabled

### Database Optimization
- [ ] 8 critical indexes added via migration
- [ ] N+1 query in get_quiz_attempt_history fixed with subqueries
- [ ] Current user query optimized with selectinload
- [ ] Connection pooling config: pool_size=20, max_overflow=40
- [ ] PgBouncer config template provided
- [ ] Redis caching strategy defined (lesson content, progress, leaderboard)
- [ ] Backup script with S3 upload + cron job
- [ ] SQLite → PostgreSQL migration gotchas documented

### AI / LLM Integration
- [ ] Claude 3.5 Sonnet selected as provider
- [ ] RAG pipeline service with pgvector similarity search
- [ ] Streaming chat endpoint using SSE + partial message saves
- [ ] Mongolian STEM tutor system prompt created
- [ ] Token counting + daily message limits via Redis
- [ ] LLM budget middleware protecting per-user quotas

### Performance & Scaling
- [ ] Celery Redis broker configured explicitly (not in-memory)
- [ ] Celery health check endpoint added
- [ ] 5 async blocking anti-patterns documented + ruff rule suggested
- [ ] Locust load test script covering 3 flows
- [ ] Load test success criteria defined (p95 <500ms, p99 <2s, <0.1% errors)
- [ ] Cloudflare free tier setup for static assets
- [ ] Exam season scaling playbook (1-page runbook with exact steps)

---

**Estimated Total Implementation Time: 60-80 engineering hours**  
**Recommended Team: 1 backend engineer (6-7 weeks at 10h/week) + 1 DevOps engineer (3-4 weeks)**

