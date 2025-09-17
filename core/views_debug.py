from django.http import JsonResponse
from django.contrib.auth import get_user_model, authenticate
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json

User = get_user_model()

@csrf_exempt
def debug_auth(request):
    """Debug endpoint to test authentication"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            # Check if user exists
            try:
                user = User.objects.get(username=username)
                user_exists = True
                user_info = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'user_type': user.user_type,
                    'is_active': user.is_active,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                }
            except User.DoesNotExist:
                user_exists = False
                user_info = None
            
            # Test authentication
            auth_user = authenticate(request, username=username, password=password)
            auth_success = auth_user is not None
            
            return JsonResponse({
                'user_exists': user_exists,
                'user_info': user_info,
                'auth_success': auth_success,
                'total_users': User.objects.count(),
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    # GET request - show current user status
    return JsonResponse({
        'authenticated': request.user.is_authenticated,
        'user': request.user.username if request.user.is_authenticated else None,
        'total_users': User.objects.count(),
        'all_users': list(User.objects.values('username', 'email', 'user_type', 'is_active'))
    })

@login_required
def debug_user(request):
    """Debug endpoint to show current user"""
    return JsonResponse({
        'username': request.user.username,
        'email': request.user.email,
        'user_type': request.user.user_type,
        'is_staff': request.user.is_staff,
        'is_superuser': request.user.is_superuser,
        'groups': list(request.user.groups.values_list('name', flat=True)),
    })