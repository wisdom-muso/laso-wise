"""
Health check endpoint for Docker container monitoring
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import redis
import time


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Comprehensive health check for the application
    """
    health_status = {
        'status': 'healthy',
        'timestamp': time.time(),
        'checks': {}
    }
    
    # Database health check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = {'status': 'healthy'}
    except Exception as e:
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'unhealthy'
    
    # Cache/Redis health check
    try:
        cache.set('health_check', 'ok', timeout=60)
        cache_value = cache.get('health_check')
        if cache_value == 'ok':
            health_status['checks']['cache'] = {'status': 'healthy'}
        else:
            health_status['checks']['cache'] = {
                'status': 'unhealthy',
                'error': 'Cache value mismatch'
            }
            health_status['status'] = 'unhealthy'
    except Exception as e:
        health_status['checks']['cache'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'unhealthy'
    
    # Redis direct check (if configured)
    if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
        try:
            r = redis.from_url(settings.REDIS_URL)
            r.ping()
            health_status['checks']['redis'] = {'status': 'healthy'}
        except Exception as e:
            health_status['checks']['redis'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['status'] = 'unhealthy'
    
    # Application-specific checks
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user_count = User.objects.count()
        health_status['checks']['application'] = {
            'status': 'healthy',
            'user_count': user_count
        }
    except Exception as e:
        health_status['checks']['application'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'unhealthy'
    
    # Return appropriate HTTP status code
    status_code = 200 if health_status['status'] == 'healthy' else 503
    
    return JsonResponse(health_status, status=status_code)


@csrf_exempt
@require_http_methods(["GET"])
def readiness_check(request):
    """
    Readiness check for Kubernetes/container orchestration
    """
    try:
        # Basic database connectivity check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({'status': 'ready'}, status=200)
    except Exception as e:
        return JsonResponse({
            'status': 'not_ready',
            'error': str(e)
        }, status=503)


@csrf_exempt
@require_http_methods(["GET"])
def liveness_check(request):
    """
    Liveness check for Kubernetes/container orchestration
    """
    return JsonResponse({'status': 'alive'}, status=200)