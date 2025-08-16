# This file makes the views directory a Python package
from .base_views import home, TermsView, PrivacyView
from .analytics import analytics_dashboard, analytics_api
from .health import health_check, health_detailed, readiness_check, liveness_check, metrics

# Import views from the parent views.py file that are not in the views package
from ..views import IndexView, csrf_token_view