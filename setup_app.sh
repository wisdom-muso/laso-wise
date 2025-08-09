#!/bin/bash

# This script ensures the proper directory structure and files exist
# before running the Django application

echo "Setting up application directory structure..."

# Create necessary directories
mkdir -p core/views
mkdir -p staticfiles
mkdir -p media
mkdir -p logs

# Ensure __init__.py files exist in all Python package directories
find . -type d -not -path "*/\.*" -not -path "*/venv*" -not -path "*/staticfiles*" -not -path "*/media*" -not -path "*/logs*" -exec touch {}/__init__.py \;

# Specifically ensure core/views/__init__.py exists and has the correct imports
if [ -f "core/views/__init__.py" ]; then
    # Check if the file is empty or doesn't have the required imports
    if ! grep -q "from .base_views import" "core/views/__init__.py" && ! grep -q "from .analytics import" "core/views/__init__.py"; then
        echo "# This file makes the views directory a Python package
from .base_views import home, TermsView, PrivacyView
from .analytics import analytics_dashboard, analytics_api
from .health import health_check, health_detailed, readiness_check, liveness_check, metrics" > core/views/__init__.py
        echo "Updated core/views/__init__.py with proper imports"
    fi
else
    echo "# This file makes the views directory a Python package
from .base_views import home, TermsView, PrivacyView
from .analytics import analytics_dashboard, analytics_api
from .health import health_check, health_detailed, readiness_check, liveness_check, metrics" > core/views/__init__.py
    echo "Created core/views/__init__.py with proper imports"
fi

# Ensure the health.py file exists in core/views
if [ ! -f "core/views/health.py" ]; then
    echo "Creating core/views/health.py with health check endpoints..."
    cat > core/views/health.py << 'EOF'
"""
Health check views for monitoring and deployment
"""
import json
import time
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
@csrf_exempt
def health_check(request):
    """
    Simple health check endpoint for load balancers and monitoring
    Returns 200 OK if the application is running
    """
    return HttpResponse("healthy\n", content_type="text/plain")


@require_http_methods(["GET"])
@csrf_exempt
def health_detailed(request):
    """
    Detailed health check with component status
    Returns JSON with detailed health information
    """
    start_time = time.time()
    health_status = {
        "status": "healthy",
        "timestamp": timezone.now().isoformat(),
        "version": getattr(settings, 'VERSION', 'unknown'),
        "environment": "production" if not settings.DEBUG else "development",
        "checks": {}
    }
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
        logger.error(f"Database health check failed: {e}")
    
    # Cache check (if Redis is configured)
    try:
        cache_key = f"health_check_{int(time.time())}"
        cache.set(cache_key, "test", 30)
        cache_value = cache.get(cache_key)
        if cache_value == "test":
            cache.delete(cache_key)
            health_status["checks"]["cache"] = {
                "status": "healthy",
                "message": "Cache is working"
            }
        else:
            health_status["checks"]["cache"] = {
                "status": "degraded",
                "message": "Cache set/get test failed"
            }
    except Exception as e:
        health_status["checks"]["cache"] = {
            "status": "unavailable",
            "message": f"Cache unavailable: {str(e)}"
        }
    
    # Disk space check
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        free_gb = free // (2**30)  # Convert to GB
        
        if free_gb < 1:  # Less than 1GB free
            health_status["status"] = "unhealthy"
            health_status["checks"]["disk_space"] = {
                "status": "critical",
                "message": f"Low disk space: {free_gb}GB free"
            }
        elif free_gb < 5:  # Less than 5GB free
            health_status["checks"]["disk_space"] = {
                "status": "warning",
                "message": f"Disk space getting low: {free_gb}GB free"
            }
        else:
            health_status["checks"]["disk_space"] = {
                "status": "healthy",
                "message": f"Disk space OK: {free_gb}GB free"
            }
    except Exception as e:
        health_status["checks"]["disk_space"] = {
            "status": "unknown",
            "message": f"Could not check disk space: {str(e)}"
        }
    
    # Response time
    response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    health_status["response_time_ms"] = round(response_time, 2)
    
    # If response time is too high, mark as degraded
    if response_time > 5000:  # 5 seconds
        health_status["status"] = "degraded"
    
    # Determine HTTP status code
    if health_status["status"] == "healthy":
        status_code = 200
    elif health_status["status"] == "degraded":
        status_code = 200  # Still return 200 but with degraded status
    else:
        status_code = 503  # Service Unavailable
    
    return JsonResponse(health_status, status=status_code)


@require_http_methods(["GET"])
@csrf_exempt
def readiness_check(request):
    """
    Readiness check for Kubernetes/container orchestration
    Returns 200 if the application is ready to serve traffic
    """
    try:
        # Check database connectivity
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        return HttpResponse("ready\n", content_type="text/plain")
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return HttpResponse(
            f"not ready: {str(e)}\n",
            content_type="text/plain",
            status=503
        )


@require_http_methods(["GET"])
@csrf_exempt
def liveness_check(request):
    """
    Liveness check for Kubernetes/container orchestration
    Returns 200 if the application process is alive
    """
    return HttpResponse("alive\n", content_type="text/plain")


@require_http_methods(["GET"])
@csrf_exempt
def metrics(request):
    """
    Basic metrics endpoint for monitoring
    Returns simple text metrics in Prometheus format
    """
    try:
        # Get database connection count
        db_connections = len(connection.queries) if settings.DEBUG else 0
        
        # Get basic system metrics
        import psutil
        import os
        
        # Memory usage
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        # CPU usage
        cpu_percent = process.cpu_percent()
        
        metrics_text = f"""# HELP django_app_info Application information
# TYPE django_app_info gauge
django_app_info{{version="{getattr(settings, 'VERSION', 'unknown')}"}} 1

# HELP django_memory_usage_bytes Memory usage in bytes
# TYPE django_memory_usage_bytes gauge
django_memory_usage_bytes {memory_info.rss}

# HELP django_cpu_usage_percent CPU usage percentage
# TYPE django_cpu_usage_percent gauge
django_cpu_usage_percent {cpu_percent}

# HELP django_db_connections Database connections
# TYPE django_db_connections gauge
django_db_connections {db_connections}

# HELP django_health_status Application health status (1=healthy, 0=unhealthy)
# TYPE django_health_status gauge
django_health_status 1
"""
        
        return HttpResponse(metrics_text, content_type="text/plain")
        
    except ImportError:
        # psutil not available, return basic metrics
        metrics_text = f"""# HELP django_app_info Application information
# TYPE django_app_info gauge
django_app_info{{version="{getattr(settings, 'VERSION', 'unknown')}"}} 1

# HELP django_health_status Application health status (1=healthy, 0=unhealthy)
# TYPE django_health_status gauge
django_health_status 1
"""
        return HttpResponse(metrics_text, content_type="text/plain")
    
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        return HttpResponse(
            "# Error generating metrics\n",
            content_type="text/plain",
            status=500
        )
EOF
fi

# Ensure the base_views.py file exists in core/views
if [ ! -f "core/views/base_views.py" ]; then
    echo "Creating core/views/base_views.py with basic view functions..."
    echo 'from django.http import HttpResponse, HttpRequest
from django.shortcuts import render
from django.views.generic import TemplateView

from accounts.models import User
from core.constants import USER_ROLE_DOCTOR


def home(request: HttpRequest) -> HttpResponse:
    doctors = (
        User.objects.select_related("profile")
        .filter(role=USER_ROLE_DOCTOR)
        .filter(is_superuser=False)
    )
    return render(request, "home.html", {"doctors": doctors})


class TermsView(TemplateView):
    template_name = "core/terms.html"


class PrivacyView(TemplateView):
    template_name = "core/privacy.html"' > core/views/base_views.py
fi

# Ensure the analytics.py file exists in core/views
if [ ! -f "core/views/analytics.py" ]; then
    echo "Creating core/views/analytics.py with analytics view functions..."
    # Copy the analytics view functions from views.py if it exists
    if [ -f "core/views.py" ]; then
        grep -A 200 "def analytics_dashboard" core/views.py > core/views/analytics.py
        # Add necessary imports at the top
        sed -i '1s/^/from django.shortcuts import render\nfrom django.http import JsonResponse\nfrom django.contrib.admin.views.decorators import staff_member_required\nfrom django.db.models import Count, Q, Avg\nfrom django.utils import timezone\nfrom datetime import datetime, timedelta\n\nfrom accounts.models import User\nfrom bookings.models import Booking, Prescription\nfrom core.models import Review\nfrom core.constants import (\n    USER_ROLE_DOCTOR, USER_ROLE_PATIENT,\n    BOOKING_STATUS_PENDING, BOOKING_STATUS_CONFIRMED,\n    BOOKING_STATUS_COMPLETED, BOOKING_STATUS_CANCELLED,\n    DAYS_RECENT, DAYS_LAST_WEEK, MONTHS_TREND\n)\n\n/' core/views/analytics.py
    else
        echo "WARNING: Could not create analytics.py from views.py. The file will need to be created manually."
    fi
fi

# Ensure the constants.py file exists
if [ ! -f "core/constants.py" ]; then
    echo "Creating core/constants.py with application constants..."
    echo '"""
Constants for the core application.
This file centralizes hardcoded values that were previously scattered throughout the codebase.
"""

# User roles
USER_ROLE_DOCTOR = "doctor"
USER_ROLE_PATIENT = "patient"
USER_ROLE_ADMIN = "admin"
USER_ROLE_STAFF = "staff"

USER_ROLES = (
    (USER_ROLE_DOCTOR, "Doctor"),
    (USER_ROLE_PATIENT, "Patient"),
    (USER_ROLE_ADMIN, "Admin"),
    (USER_ROLE_STAFF, "Staff"),
)

# Booking status
BOOKING_STATUS_PENDING = "pending"
BOOKING_STATUS_CONFIRMED = "confirmed"
BOOKING_STATUS_COMPLETED = "completed"
BOOKING_STATUS_CANCELLED = "cancelled"

BOOKING_STATUSES = (
    (BOOKING_STATUS_PENDING, "Pending"),
    (BOOKING_STATUS_CONFIRMED, "Confirmed"),
    (BOOKING_STATUS_COMPLETED, "Completed"),
    (BOOKING_STATUS_CANCELLED, "Cancelled"),
)

# Time periods for analytics
DAYS_RECENT = 30
DAYS_LAST_WEEK = 7
MONTHS_TREND = 6

# Pagination
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100

# File upload limits
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB

# Review ratings
MIN_RATING = 1
MAX_RATING = 5' > core/constants.py
fi

echo "Application directory structure setup complete."