"""Celery configuration for EduSpark."""
from celery import Celery
from app.core.config import settings

celery_app = Celery("eduspark")

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
    task_time_limit=3600,
    task_soft_time_limit=3300,
)


@celery_app.task(bind=True, max_retries=3)
def example_async_task(self, user_id: str):
    """Example async task with retry logic."""
    try:
        # Do work here
        pass
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
