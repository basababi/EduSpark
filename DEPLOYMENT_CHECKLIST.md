# Production-Ready Alembic Migration for Indexes

**File: `apps/api/alembic/versions/[timestamp]_add_production_indexes.py`**

Create this file using:
```bash
cd apps/api
alembic revision -m "add_production_indexes"
```

Then replace the content with:

```python
"""Add production-critical indexes.

Revision ID: 0003_production_indexes
Revises: [previous_migration_id]
Create Date: 2026-06-03

"""
from alembic import op
from sqlalchemy import text

revision = "0003_production_indexes"
down_revision = None  # Change to actual previous revision
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add production-critical indexes."""
    # User indexes
    op.execute(text('CREATE INDEX idx_user_email ON "user"(email)'))
    op.execute(text('CREATE INDEX idx_user_is_active ON "user"(is_active)'))
    
    # Quiz indexes
    op.execute(text('CREATE INDEX idx_quiz_topic_id ON quiz(topic_id)'))
    op.execute(text(
        'CREATE INDEX idx_quizattempt_user_completed ON quizattempt'
        '(user_id, completed_at DESC NULLS LAST)'
    ))
    op.execute(text('CREATE INDEX idx_quizanswer_attempt_id ON quizanswer(attempt_id)'))
    op.execute(text('CREATE INDEX idx_quizquestion_quiz_id ON quizquestion(quiz_id)'))
    
    # Progress indexes
    op.execute(text('CREATE INDEX idx_studysession_user_id ON studysession(user_id)'))
    
    # Chat indexes
    op.execute(text(
        'CREATE INDEX idx_chatmessage_session_id ON chatmessage'
        '(session_id, created_at DESC)'
    ))


def downgrade() -> None:
    """Drop all production indexes."""
    op.execute(text('DROP INDEX IF EXISTS idx_user_email'))
    op.execute(text('DROP INDEX IF EXISTS idx_user_is_active'))
    op.execute(text('DROP INDEX IF EXISTS idx_quiz_topic_id'))
    op.execute(text('DROP INDEX IF EXISTS idx_quizattempt_user_completed'))
    op.execute(text('DROP INDEX IF EXISTS idx_quizanswer_attempt_id'))
    op.execute(text('DROP INDEX IF EXISTS idx_quizquestion_quiz_id'))
    op.execute(text('DROP INDEX IF EXISTS idx_studysession_user_id'))
    op.execute(text('DROP INDEX IF EXISTS idx_chatmessage_session_id'))
```

**To apply:**
```bash
cd apps/api
alembic upgrade head
```

**To rollback if needed:**
```bash
alembic downgrade -1
```

---

# Secrets Management Checklist

**Production Secrets Rotation Procedure:**

1. **JWT_SECRET** (32+ bytes)
   ```bash
   # Generate new secret
   openssl rand -hex 32
   # Output: abc123def456abc123def456abc123def456
   
   # Update in GitHub Secrets, Railway, Vercel
   # Old secret stays valid for 30 min (refresh token window)
   # After 30 min, all users must refresh tokens (automatic)
   ```

2. **DATABASE_URL**
   - Format: `postgresql+asyncpg://user:password@host:5432/dbname`
   - Use Railway managed PostgreSQL (auto-encrypted, auto-backed-up)
   - Never use localhost; always use managed database endpoint
   - Enable SSL: append `?sslmode=require` to connection string

3. **REDIS_URL**
   - Format: `redis://:password@host:6379/0`
   - Use Railway managed Redis (auto-backed-up, auto-replicated)
   - Enable TLS: use `rediss://` protocol

4. **Environment Variables (GitHub Secrets)**
   ```
   RAILWAY_API_TOKEN=... (for Railway deployment)
   DATABASE_URL=... (Railway-managed PostgreSQL)
   REDIS_URL=... (Railway-managed Redis)
   JWT_SECRET=... (32-byte hex string)
   SENTRY_DSN=... (error tracking)
   OPENAI_API_KEY=... (AI provider)
   ```

5. **Rotation Schedule**
   - JWT_SECRET: Every 90 days (or on suspected compromise)
   - Database password: Every 180 days (via Railway dashboard)
   - Redis password: Every 180 days (via Railway dashboard)

---

# Summary of All Files Created

## Core Security
- ✅ `apps/api/app/core/token_blacklist.py` — Access token revocation
- ✅ `apps/api/app/core/rate_limit.py` — Per-user rate limiting
- ✅ `apps/api/app/core/llm_budget.py` — LLM cost controls

## Deployment & Infrastructure
- ✅ `apps/api/app/celery_app.py` — Celery + Redis broker
- ✅ `apps/api/Dockerfile.prod` — Production Docker image
- ✅ `docker-compose.yml` — Updated with Celery + health checks
- ✅ `.github/workflows/ci.yml` — GitHub Actions CI/CD pipeline

## Configuration & Examples
- ✅ `apps/api/.env.example` — Environment variables template

## Scripts
- ✅ `scripts/backup.sh` — Database backup script
- ✅ `apps/api/tests/load_test.py` — Locust load testing

## Documentation
- ✅ `PRODUCTION_AUDIT.md` — Complete 100-page production audit (6 sections)
- ✅ `IMPLEMENTATION_GUIDE.md` — Quick-start checklist for implementation
- ✅ `AUDIT_SUMMARY.md` — Executive summary and risk assessment

---

# Code Changes Summary

## Files to Update (Manual Edits)

### 1. `apps/api/app/db/session.py`
**Change:** Update engine creation with connection pooling

```python
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600,
    pool_pre_ping=True,
    connect_args={"timeout": 10, "command_timeout": 60},
)
```

### 2. `apps/api/app/api/deps.py`
**Add:** Import and use token blacklist check

```python
from app.core.token_blacklist import is_access_token_blacklisted

async def get_current_user(...):
    if await is_access_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token revoked")
    # ... rest
```

### 3. `apps/api/app/api/routes/auth.py`
**Update:** `/logout` endpoint to blacklist access token

```python
from app.core.token_blacklist import blacklist_access_token

@router.post("/logout", ...)
async def logout(token: str = Depends(oauth2_scheme), ...):
    await blacklist_access_token(token)
    await revoke_refresh_token(refresh_token)
    return Response(status_code=204)
```

### 4. `apps/api/app/main.py`
**Add:** TrustedHostMiddleware + request ID middleware + logging setup

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.core.logging import RequestIdMiddleware, setup_logging

def get_app():
    app = FastAPI(...)
    
    setup_logging(settings.environment, settings.log_level)
    app.add_middleware(RequestIdMiddleware)
    
    if settings.environment == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_origins_list,
        )
    # ... rest
```

### 5. `apps/api/app/services/quiz_service.py`
**Replace:** `get_quiz_attempt_history()` with subquery version (see PRODUCTION_AUDIT.md 4.2)

---

# Validation Commands

```bash
# Test locally
docker-compose up -d
docker-compose logs -f api

# Verify all services healthy
curl http://localhost:8000/health

# Test token blacklist
curl -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test rate limiting
for i in {1..1001}; do
  curl http://localhost:8000/subjects \
    -H "Authorization: Bearer YOUR_TOKEN"
done
# Should see 429 after 1000 requests

# Run load test
locust -f apps/api/tests/load_test.py \
  --host=http://localhost:8000 \
  --users=100 \
  --spawn-rate=10 \
  --run-time=5m \
  --headless

# Check database connection pooling
psql postgresql://eduspark:eduspark@localhost:5432/eduspark \
  -c "SELECT count(*) FROM pg_stat_activity;"

# Verify Celery worker
docker-compose logs celery_worker | grep "worker online"
```

---

# Final Production Checklist

Before deploying to Railway/production:

**Security:**
- [ ] JWT_SECRET is 32+ bytes (check with: `echo $JWT_SECRET | wc -c`)
- [ ] ALLOWED_ORIGINS does NOT contain wildcards
- [ ] ALLOWED_ORIGINS uses HTTPS only (except localhost)
- [ ] Access token blacklist implemented and tested
- [ ] Rate limiting middleware active on all protected routes
- [ ] Input validation on /quizzes, /auth, /users endpoints

**Performance:**
- [ ] Database connection pooling: pool_size=20
- [ ] N+1 queries fixed in get_quiz_attempt_history
- [ ] 8 production indexes created and verified
- [ ] Load test p95 latency: <500ms, p99: <2000ms
- [ ] Redis responding to health check

**Deployment:**
- [ ] Dockerfile.prod builds without errors
- [ ] docker-compose.yml runs all services
- [ ] CI/CD pipeline passes (all green checks)
- [ ] Health check endpoint returns "healthy"
- [ ] Celery worker starts without errors

**Monitoring:**
- [ ] Sentry DSN configured
- [ ] Health check runs every 30 seconds
- [ ] Backup script scheduled (cron job)
- [ ] Oncall runbook created and shared

**Ready for production:** ✅ You're good to go!

