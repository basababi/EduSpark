# EduSpark AI – Mongolian STEM Learning Platform

Production-grade MVP that provides AI чат багш, тест үүсгэлт, ахиц хяналт, болон админ контент менежмент. Monorepo with Next.js фронтэнд + FastAPI бэкэнд, PostgreSQL + pgvector өгөгдлийн сан, Redis, Docker-compose орчин.

## Хурдан эхлүүлэх

1. **Шаардлага**: Docker + Docker Compose, Node 20+, Python 3.11+, Make (optional).
2. **Орчин тохируулах**  
   ```bash
   cp .env.example .env
   # .env доторх түлхүүрүүдийг шинэчилнэ (JWT_SECRET гэх мэт)
   ```
3. **Docker-оор ажиллуулах**  
   ```bash
   docker compose up --build
   ```
   - `web`: Next.js app (http://localhost:3000)  
   - `api`: FastAPI app (http://localhost:8000/docs)
   - `db`: PostgreSQL + pgvector  
   - `redis`: Cache/queues

4. **Локал хөгжүүлэлт (сонголт)**  
   ```bash
   # Frontend
   cd apps/web && npm install && npm run dev
   # Backend
   cd ../api && python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   alembic upgrade head
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Гол модулиуд
- `apps/web`: Next.js App Router + Tailwind + shadcn/ui хэв маягийн компонентүүд.
- `apps/api`: FastAPI, SQLAlchemy 2.0, Alembic, JWT RBAC, RAG бэлтгэл.
- `docs/`: Архитектур, API, prompt, deployment баримт.
- `docker-compose.yml`: Prod-ready dev stack.

## Фазын төлөв (MVP roadmap)
- **Phase 1 (энэ код)**: Scaffold, auth, landing page, dashboard shell, үндсэн схемүүд, анхны миграци, seed.
- Phase 2: Subject/topic/lesson flows, AI chat UI/endpoint, quiz engine, progress tracking.
- Phase 3: Document ingestion + retrieval pipeline, admin panel, citations.
- Phase 4: Polish, tests, CI/CD, observability, hardening.

## Шаардлагатай env түлхүүрүүд
- `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `JWT_EXPIRES_MIN`, `REFRESH_EXPIRES_MIN`, `OPENAI_API_KEY` (optional), `NEXT_PUBLIC_API_URL`

## Лиценз
Internal MVP – modify as needed.
