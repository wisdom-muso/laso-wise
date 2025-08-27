from __future__ import annotations

# Ensure Celery app is always imported when Django starts
try:
    from .celery import app as celery_app  # noqa: F401
except Exception:
    # Celery is optional; avoid hard crash if not configured
    celery_app = None

__all__ = ("celery_app",)

