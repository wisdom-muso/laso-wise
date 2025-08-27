from __future__ import annotations

import os
from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meditrack.settings")

celery_app = Celery("meditrack")

# Load Celery settings from Django settings with CELERY_ namespace
celery_app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py in installed apps
celery_app.autodiscover_tasks()


@celery_app.task(bind=True)
def debug_task(self):
    return f"Request: {self.request!r}"

