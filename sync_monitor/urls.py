from django.urls import path
from . import views

app_name = 'sync_monitor'

urlpatterns = [
    path('', views.SyncDashboardView.as_view(), name='dashboard'),
    path('sync/<int:pk>/', views.SyncStatusDetailView.as_view(), name='sync_detail'),
    path('trigger-sync/', views.TriggerSyncView.as_view(), name='trigger_sync'),
    path('health-check/', views.PerformHealthCheckView.as_view(), name='health_check'),
    path('health-history/', views.SystemHealthHistoryView.as_view(), name='health_history'),
    path('api/health-status/', views.SystemHealthAPIView.as_view(), name='health_api'),
]