from django.urls import path
from django.contrib import admin
from django.views.generic import TemplateView

from . import views
from .admin_views import (
    EnhancedAdminDashboardView, 
    vitals_analytics_api, 
    telemedicine_config_api
)

app_name = 'core'

urlpatterns = [
    # Public pages
    path('', views.IndexView.as_view(), name='index'),
    path('about/', TemplateView.as_view(template_name='core/about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='core/contact.html'), name='contact'),
    path('services/', TemplateView.as_view(template_name='core/services.html'), name='services'),
    
    # Enhanced Admin Dashboard
    path('admin/enhanced-dashboard/', EnhancedAdminDashboardView.as_view(), name='enhanced-admin-dashboard'),
    
    # Admin Analytics APIs
    path('admin/analytics/vitals/', vitals_analytics_api, name='vitals-analytics-api'),
    path('admin/analytics/telemedicine-config/', telemedicine_config_api, name='telemedicine-config-api'),
    
    # API endpoints
    path('api/health/', views.health_check, name='health_check'),
    path('api/csrf/', views.csrf_token_view, name='csrf_token'),
]
