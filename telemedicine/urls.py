from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'telemedicine'

# Create router for viewsets
router = DefaultRouter()
router.register(r'consultations', views.ConsultationViewSet, basename='consultations')
router.register(r'video-providers', views.VideoProviderViewSet, basename='video-providers')
router.register(r'technical-issues', views.TechnicalIssueViewSet, basename='technical-issues')
router.register(r'bookings', views.BookingConsultationViewSet, basename='booking-consultations')

urlpatterns = [
    path('api/', include(router.urls)),
]