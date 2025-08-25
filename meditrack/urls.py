"""
URL configuration for meditrack project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from core.forms import LoginForm
from core.views import HomeView, dashboard
from core.views_auth import CustomLoginView, HomeRedirectView
from core.logout_view import logout_view
from core.views_theme import toggle_theme, get_theme_preference
from core.health_check import health_check, readiness_check, liveness_check

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Home page - redirect to login if not authenticated, otherwise to dashboard
    path('', HomeRedirectView.as_view(), name='home'),
    path('landing/', HomeView.as_view(), name='landing'),
    
    # Dashboard
    path('dashboard/', dashboard, name='dashboard'),
    
    # Authentication
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    
    # Theme settings
    path('theme/toggle/', toggle_theme, name='toggle-theme'),
    path('theme/preference/', get_theme_preference, name='get-theme-preference'),
    
    # Health check endpoints
    path('health/', health_check, name='health-check'),
    path('readiness/', readiness_check, name='readiness-check'),
    path('liveness/', liveness_check, name='liveness-check'),
    
    # Core app URLs
    path('core/', include('core.urls', namespace='core')),
    
    # Appointments app URLs
    path('appointments/', include('appointments.urls')),
    
    # Treatments app URLs
    path('treatments/', include('treatments.urls')),
    
    # Telemedicine app URLs
    path('telemedicine/', include('telemedicine.urls')),
]

# Media and static files URLs
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
