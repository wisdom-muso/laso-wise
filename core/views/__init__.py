# This file makes the views directory a Python package
from .base_views import home, TermsView, PrivacyView, IndexView, csrf_token_view
from .analytics import analytics_dashboard, analytics_api
from .health import health_check, health_detailed, readiness_check, liveness_check, metrics