from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Avg

from .views import home, analytics_api
from .api import (
    SoapNoteViewSet, EHRRecordViewSet, AuditLogViewSet, PatientSearchViewSet,
    get_csrf_token, health_check, CustomAuthToken, 
    register_user, logout_user, get_current_user, dashboard_stats
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
    
    # Authentication endpoints
    path('api/auth/login/', CustomAuthToken.as_view(), name='api_login'),
    path('api/auth/register/', register_user, name='api_register'),
    path('api/auth/logout/', logout_user, name='api_logout'),
    path('api/auth/me/', get_current_user, name='api_current_user'),
    
    # Utility endpoints
    path('api/csrf/', get_csrf_token, name='api_csrf'),
    path('api/health/', health_check, name='api_health'),
    
    # Dashboard endpoints
    path('api/dashboard/stats/', dashboard_stats, name='api_dashboard_stats'),
    
    # Analytics API (admin only)
    path("analytics/api/", staff_member_required(analytics_api), name="analytics-api"),
]
