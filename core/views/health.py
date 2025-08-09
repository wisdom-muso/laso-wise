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
