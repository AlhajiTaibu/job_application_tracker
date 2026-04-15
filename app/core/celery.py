from celery import Celery
from app.core.config import settings

# Initialize Celery
celery_app = Celery(
    "worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['app.tasks.email_tasks']
)

celery_app.autodiscover_tasks()

# Production Optimizations
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1 # Prevents one worker from hogging all tasks
)

