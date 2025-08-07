from django.urls import path
from django.shortcuts import redirect
from .views import home, TermsView, PrivacyView, analytics_dashboard, analytics_api

app_name = "core"

def redirect_to_doctors(request):
    return redirect('doctors:list')

urlpatterns = [
    path("", redirect_to_doctors, name="home"),
    path("home/", home, name="home-page"),
    path("terms/", TermsView.as_view(), name="terms"),
    path("privacy/", PrivacyView.as_view(), name="privacy"),
    path("admin/analytics/", analytics_dashboard, name="analytics-dashboard"),
    path("admin/analytics/api/", analytics_api, name="analytics-api"),
]
