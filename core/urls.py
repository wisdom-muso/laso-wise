from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Avg

from .views import home, analytics_api
from .api import (
    SoapNoteViewSet, EHRRecordViewSet, AuditLogViewSet, PatientSearchViewSet
)

# Create router for API viewsets
router = DefaultRouter()
router.register(r'soap-notes', SoapNoteViewSet, basename='soap-notes')
router.register(r'ehr', EHRRecordViewSet, basename='ehr')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-logs')
router.register(r'patient-search', PatientSearchViewSet, basename='patient-search')

app_name = "core"

urlpatterns = [
    path("", home, name="home"),
    
    # API endpoints
    path("api/", include(router.urls)),
    
    # Analytics API (admin only)
    path("analytics/api/", staff_member_required(analytics_api), name="analytics-api"),
]
