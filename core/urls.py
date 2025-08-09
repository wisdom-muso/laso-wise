from django.urls import path
from django.shortcuts import redirect
# Import from the views package
from core.views import (
    home, TermsView, PrivacyView, 
    analytics_dashboard, analytics_api,
    health_check, health_detailed, readiness_check, 
    liveness_check, metrics
)

app_name = "core"

def redirect_to_doctors(request):
    return redirect('doctors:list')

urlpatterns = [
    path("", redirect_to_doctors, name="home"),
    path("home/", home, name="home-page"),
    path("terms/", TermsView.as_view(), name="terms"),
    path("privacy/", PrivacyView.as_view(), name="privacy"),
    path("", analytics_dashboard, name="analytics-dashboard"),
    path("api/", analytics_api, name="analytics-api"),
    
    # Health check endpoints
    path("health/", health_check, name="health"),
    path("health/detailed/", health_detailed, name="health-detailed"),
    path("health/ready/", readiness_check, name="readiness"),
    path("health/live/", liveness_check, name="liveness"),
    path("metrics/", metrics, name="metrics"),
]
