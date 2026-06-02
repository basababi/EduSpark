from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, health, learning, progress, quizzes, users
from app.core.config import settings
from app.db.redis import close_redis_client


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_redis_client()


def get_app() -> FastAPI:
    app = FastAPI(title=settings.project_name, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(learning.router)
    app.include_router(quizzes.router)
    app.include_router(progress.router)
    return app


app = get_app()
