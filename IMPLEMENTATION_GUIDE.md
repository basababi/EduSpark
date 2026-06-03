# QUICK-START IMPLEMENTATION GUIDE

**EduSpark Production-Readiness: Fastest Path to Launch**

---

## CRITICAL (Start Here - 24 Hours)

### 1. Add Access Token Blacklist
✅ File created: `apps/api/app/core/token_blacklist.py`

**Apply changes to:**
- `apps/api/app/api/deps.py` line 18: Add blacklist check to `get_current_user()`
- `apps/api/app/api/routes/auth.py` line 79: Update `/logout` to blacklist access token

**Code snippet for deps.py:**
```python
async def get_current_user(...):
    from app.core.token_blacklist import is_access_token_blacklisted
    
    if await is_access_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token revoked")
    
    # ... rest of function
```

### 2. Update Database Config
✅ File ready: `apps/api/app/db/session.py` needs pooling update

**Replace the engine creation with:**
```python
engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600,
    pool_pre_ping=True,
)
```

### 3. Update CORS Config
**File: `apps/api/app/main.py`** - Add before CORS middleware:
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_origins_list,
    )
```

### 4. Enable Celery
✅ File created: `apps/api/app/celery_app.py`

**Add to imports in routes that need tasks:**
```python
from app.celery_app import celery_app

@celery_app.task
def async_task(user_id: str):
    pass
```

### 5. Update docker-compose.yml
✅ Already updated with Celery worker and health checks

**Test locally:**
```bash
docker-compose up -d
docker-compose logs -f api
```

---

## HIGH (Week 1 - 40 hours)

### 6. N+1 Query Fixes
**File: `apps/api/app/services/quiz_service.py`**

Replace `get_quiz_attempt_history()` (line 297) with the subquery version from PRODUCTION_AUDIT.md section 4.2

### 7. Rate Limiting
✅ File created: `apps/api/app/core/rate_limit.py`

**Add to deps.py:**
```python
from app.core.rate_limit import check_rate_limit

async def rate_limit_check(user: User = Depends(get_current_user)):
    allowed, remaining = await check_rate_limit(user.id, limit=1000, window_seconds=60)
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return user
```

### 8. Dockerfile for Production
✅ File created: `apps/api/Dockerfile.prod`

**Build and test:**
```bash
docker build -f apps/api/Dockerfile.prod -t eduspark:latest apps/api/
docker run -p 8000:8000 eduspark:latest
```

### 9. Health Check Endpoint
**File: `apps/api/app/api/routes/health.py`** - Add from PRODUCTION_AUDIT.md section 2.4

### 10. CI/CD Pipeline
✅ File created: `.github/workflows/ci.yml`

**Enable in GitHub:**
1. Push this file to main branch
2. GitHub Actions auto-runs on next push

---

## MEDIUM (Week 2-3 - 40 hours)

### 11. Database Indexes
**Create migration:**
```bash
cd apps/api
alembic revision -m "add_production_indexes"
# Edit the migration file and add CREATE INDEX statements from PRODUCTION_AUDIT.md section 4.1
alembic upgrade head
```

### 12. LLM Integration (Claude)
**Add to requirements.txt:**
```
anthropic==0.28.0
```

**Implement chat endpoint:**
Use code from PRODUCTION_AUDIT.md section 5.3

### 13. Infrastructure Setup
**Recommended: Railway (https://railway.app)**
1. Create account and project
2. Connect GitHub repo
3. Add services: PostgreSQL, Redis
4. Set environment variables
5. Deploy via `git push main`

### 14. Frontend Deployment
**Switch to Vercel (https://vercel.com):**
1. Import GitHub repo
2. Set NEXT_PUBLIC_API_URL to your Railway API URL
3. Auto-deploys on push

---

## IMMEDIATE TODO CHECKLIST

**Do these NOW (4 hours):**
- [ ] Copy `token_blacklist.py` to codebase
- [ ] Copy `rate_limit.py` to codebase
- [ ] Copy `celery_app.py` to codebase
- [ ] Update `docker-compose.yml` (already done)
- [ ] Update `app/db/session.py` with pooling config
- [ ] Update `app/main.py` with TrustedHostMiddleware
- [ ] Test locally: `docker-compose up`

**This Week (20 hours):**
- [ ] Apply token blacklist to auth routes
- [ ] Add rate limiting dependency to `/subjects` endpoint
- [ ] Build and test `Dockerfile.prod`
- [ ] Fix `get_quiz_attempt_history` N+1 query
- [ ] Add health check endpoint
- [ ] Create GitHub Actions CI/CD

**Next Week (40 hours):**
- [ ] Create and run database index migration
- [ ] Setup Railway account and deploy
- [ ] Setup Vercel and deploy frontend
- [ ] Implement chat endpoint with Claude
- [ ] Load test with Locust
- [ ] Monitor first 24 hours in production

---

## VALIDATION CHECKLIST FOR LAUNCH

**Security:**
- [ ] JWT_SECRET is 32+ bytes and NOT in git
- [ ] ALLOWED_ORIGINS explicit (no wildcards in prod)
- [ ] Access tokens blacklisted on logout (test via browser)
- [ ] Rate limiting working (test with `ab -n 10000`)

**Infrastructure:**
- [ ] PostgreSQL connections: pool_size=20
- [ ] Redis is up and responding to health check
- [ ] Celery worker starts without errors
- [ ] API health check returns all services "healthy"

**Deployment:**
- [ ] Dockerfile.prod builds without errors
- [ ] Docker image runs and serves requests
- [ ] CI/CD pipeline passes (lint + test + build)
- [ ] Railway deploy succeeds

**Performance:**
- [ ] Load test p95 latency: <500ms
- [ ] Load test p99 latency: <2000ms
- [ ] Error rate: <0.1%
- [ ] N+1 queries fixed (verify in logs)

---

## SCRIPTS TO RUN

```bash
# Local development
docker-compose up -d
docker-compose logs -f

# Build production image
docker build -f apps/api/Dockerfile.prod -t eduspark:prod apps/api/

# Run load test (requires locust)
pip install locust
locust -f apps/api/tests/load_test.py --host=http://localhost:8000 --users=50 --spawn-rate=5 --run-time=5m --headless

# Database backup
./scripts/backup.sh

# Alembic migrations
cd apps/api
alembic revision --autogenerate -m "description"
alembic upgrade head
```

---

## LINKS & RESOURCES

- **Production Audit:** `apps/api/PRODUCTION_AUDIT.md` (complete 100+ page guide)
- **Railway Docs:** https://docs.railway.app
- **Vercel Docs:** https://vercel.com/docs
- **FastAPI:** https://fastapi.tiangolo.com
- **SQLAlchemy:** https://docs.sqlalchemy.org/en/20/
- **Celery:** https://docs.celeryproject.io

---

## SUPPORT & ESCALATION

**If stuck:**
1. Check `apps/api/PRODUCTION_AUDIT.md` section for your issue
2. Review actual code examples provided in each section
3. Test in local docker-compose first
4. Check GitHub Issues / Stack Overflow for specific error

**Critical path:** Access token blacklist → DB pooling → Dockerfile → CI/CD → Deployment

