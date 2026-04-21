from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# Initialize Celery
celery_app = Celery(
    "worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['app.tasks.email_tasks', 'app.tasks.job_tasks']
)

celery_app.autodiscover_tasks()


celery_app.conf.beat_schedule = {
    'flag_overdue_tasks': {
        'task': 'app.tasks.job_tasks.flag_overdue_tasks',
        'schedule': 86400.0,  # Run daily
    },
    # 'monthly-invoice-report': {
    #     'task': 'apps.invoicing.tasks.generate_monthly_invoice_report',
    #     'schedule': crontab(hour=9, minute=0, day_of_month=1),  # Monthly on 1st at 9 AM
    # },
}


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

