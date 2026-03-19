from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "worker",
    broker = settings.CELERY_BROKER_URL,
    backend = settings.CELERY_RESULT_BACKEND,
    include=["app.services.export_service"]
)

celery_app.conf.task_routes = {
    "app.services.export_service.*": {"queue": "export_queue"}
}

celery_app.autodiscover_tasks(["app.services"])
