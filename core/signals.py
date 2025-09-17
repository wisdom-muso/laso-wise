"""
Django signals for login session tracking
"""
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone
from .models_sessions import LoginSession


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@receiver(user_logged_in)
def track_user_login(sender, request, user, **kwargs):
    """Track user login"""
    try:
        # End any existing active sessions for this user
        LoginSession.objects.filter(
            user=user,
            is_active=True
        ).update(
            logout_time=timezone.now(),
            is_active=False
        )
        
        # Create new login session
        LoginSession.objects.create(
            user=user,
            login_time=timezone.now(),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            session_key=request.session.session_key,
            is_active=True
        )
    except Exception as e:
        # Log error but don't break login process
        print(f"Error tracking login session: {e}")


@receiver(user_logged_out)
def track_user_logout(sender, request, user, **kwargs):
    """Track user logout"""
    try:
        if user:
            # End active sessions for this user
            LoginSession.objects.filter(
                user=user,
                is_active=True
            ).update(
                logout_time=timezone.now(),
                is_active=False
            )
    except Exception as e:
        # Log error but don't break logout process
        print(f"Error tracking logout session: {e}")