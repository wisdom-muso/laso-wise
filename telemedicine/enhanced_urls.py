from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .enhanced_views import (
    EnhancedConsultationViewSet, VideoProviderViewSet, WebhookView,
    ConsultationRecordingViewSet, TechnicalIssueViewSet, BookingConsultationViewSet
)

app_name = 'telemedicine'

# Create router for enhanced viewsets
router = DefaultRouter()
router.register(r'consultations', EnhancedConsultationViewSet, basename='consultations')
router.register(r'video-providers', VideoProviderViewSet, basename='video-providers')
router.register(r'recordings', ConsultationRecordingViewSet, basename='recordings')
router.register(r'technical-issues', TechnicalIssueViewSet, basename='technical-issues')
router.register(r'bookings', BookingConsultationViewSet, basename='booking-consultations')

urlpatterns = [
    # Enhanced API endpoints
    path('api/', include(router.urls)),
    
    # Webhook endpoints for video providers
    path('api/webhooks/<str:provider>/', WebhookView.as_view(), name='webhook'),
    
    # Specific webhook endpoints (for convenience)
    path('api/webhooks/zoom/', WebhookView.as_view(), {'provider': 'zoom'}, name='zoom-webhook'),
    path('api/webhooks/google-meet/', WebhookView.as_view(), {'provider': 'google_meet'}, name='google-meet-webhook'),
    path('api/webhooks/jitsi/', WebhookView.as_view(), {'provider': 'jitsi'}, name='jitsi-webhook'),
]