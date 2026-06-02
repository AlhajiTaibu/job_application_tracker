from celery import Celery
from celery.schedules import crontab

from app.core.config import settings
import ssl
import socket

# Initialize Celery
celery_app = Celery(
    "worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['app.tasks.user_tasks', 'app.tasks.job_tasks', 'app.tasks.document_tasks', 'app.tasks.job_application', ]
)

celery_app.autodiscover_tasks()

celery_app.conf.beat_schedule = {
    'flag_overdue_tasks': {
        'task': 'app.tasks.job_tasks.flag_overdue_tasks',
        'schedule': 86400.0,
    },
    'send_task_reminders': {
        'task': 'app.tasks.job_tasks.send_task_reminders',
        'schedule': 86400.0,
    },
    'snooze_tasks': {
        'task': 'app.tasks.job_tasks.snooze_tasks',
        'schedule': 86400.0,
    },
    'mark_job_application_stale': {
        'task': 'app.tasks.job_application.mark_job_application_stale',
        'schedule': 86400.0,
    },
    'weekly_user_report': {
        'task': 'app.tasks.job_tasks.weekly_user_report',
        'schedule': crontab(day_of_week=0, hour=9, minute=0),
    },
    'delete_expired_otp': {
        'task': 'app.tasks.user_tasks.delete_expired_otp',
        'schedule': 86400.0
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
    worker_prefetch_multiplier=1,
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=None,  # retry forever
    worker_cancel_long_running_tasks_on_connection_loss=True,

    broker_use_ssl={
        "ssl_cert_reqs": ssl.CERT_NONE
    } if settings.is_prod else {},

    redis_backend_use_ssl={
        "ssl_cert_reqs": ssl.CERT_NONE
    } if settings.is_prod else {},

    # ↓ all transport-level options must live here
    broker_transport_options={
        "visibility_timeout": 3600,
        "socket_timeout": 30,
        "socket_connect_timeout": 30,
        "socket_keepalive": True,
        "socket_keepalive_options": {
            socket.TCP_KEEPIDLE: 60,  # not "TCP_KEEPIDLE"
            socket.TCP_KEEPINTVL: 10,
            socket.TCP_KEEPCNT: 5,
        },
        "retry_on_timeout": True,
        "health_check_interval": 25,
    },
)
