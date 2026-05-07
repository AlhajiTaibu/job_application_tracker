from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['app.tasks.user_tasks', 'app.tasks.job_tasks', 'app.tasks.document_tasks', 'app.tasks.job_application', ]
)

celery_app.autodiscover_tasks(['app.tasks'])

celery_app.conf.beat_schedule = {
    'flag_overdue_tasks': {
        'task': 'app.tasks.job_tasks.flag_overdue_tasks',
        'schedule': 86400.0,  # Run daily
    },
    'send_task_reminders': {
        'task': 'app.tasks.job_tasks.send_task_reminders',
        'schedule': 86400.0,  # Run daily
    },
    'snooze_tasks': {
        'task': 'app.tasks.job_tasks.snooze_tasks',
        'schedule': 86400.0,  # Run daily
    },
    'mark_job_application_stale': {
        'task': 'app.tasks.job_application.mark_job_application_stale',
        'schedule': 86400.0,  # Run daily
    },
    'weekly_user_report': {
        'task': 'app.tasks.job_tasks.weekly_user_report',
        'schedule': crontab(day_of_week=0, hour=9, minute=0),  # Weekly on Sundays at 9 AM
    },
    'delete_expired_otp': {
        'task': 'app.tasks.user_tasks.delete_expired_otp',
        'schedule': 60
    }
}

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    worker_pool="threads",
    worker_concurrency=4,
    worker_prefetch_multiplier=1
)
