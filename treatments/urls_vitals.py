"""
URL patterns for Vital Signs Management
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_vitals

# REST API router
router = DefaultRouter()
router.register(r'vitals', views_vitals.VitalSignViewSet, basename='vitals-api')
router.register(r'vital-alerts', views_vitals.VitalSignAlertViewSet, basename='vital-alerts-api')

app_name = 'vitals'

urlpatterns = [
    # Web interface URLs
    path('', views_vitals.VitalSignListView.as_view(), name='list'),
    path('<int:pk>/', views_vitals.VitalSignDetailView.as_view(), name='detail'),
    path('add/', views_vitals.VitalSignCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views_vitals.VitalSignUpdateView.as_view(), name='update'),
    
    # Dashboard URLs
    path('dashboard/', views_vitals.patient_vitals_dashboard, name='dashboard'),
    path('dashboard/<int:patient_id>/', views_vitals.patient_vitals_dashboard, name='patient_dashboard'),
    
    # API URLs
    path('api/latest/<int:patient_id>/', views_vitals.vitals_api_latest, name='api_latest'),
    path('api/', include(router.urls)),
]