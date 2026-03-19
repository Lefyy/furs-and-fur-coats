from celery import Celery

from app.config import settings


CELERY_TASK_DEFAULTS = {
    "autoretry_for": (Exception,),
    "retry_backoff": settings.celery_retry_backoff,
    "retry_backoff_max": settings.celery_retry_backoff_max,
    "retry_jitter": True,
    "max_retries": settings.celery_retry_count,
    "time_limit": settings.celery_task_time_limit,
    "soft_time_limit": settings.celery_task_soft_time_limit,
}


celery_app = Celery(
    "furs_and_fur_coats",
    broker=settings.resolved_celery_broker_url,
    backend=settings.resolved_celery_result_backend,
    include=[
        "app.tasks.enrichment_tasks",
        "app.tasks.product_description_tasks",
    ],
)

celery_app.conf.update(
    task_default_queue="default",
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    broker_connection_retry_on_startup=True,
    task_time_limit=settings.celery_task_time_limit,
    task_soft_time_limit=settings.celery_task_soft_time_limit,
)
