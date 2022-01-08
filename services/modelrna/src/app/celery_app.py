from celery import Celery

from app.config import get_settings

celery_app = Celery("celery_app", broker=get_settings().redis_celery_url,
                    result_backend=get_settings().redis_celery_url)
