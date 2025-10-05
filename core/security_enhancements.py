"""
Security Enhancements for Laso Healthcare System
Enterprise-grade security features and best practices
"""
import hashlib
import hmac
import secrets
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from django.db import models
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

User = get_user_model()
logger = logging.getLogger(__name__)


class SecurityAuditLog(models.Model):
    """
    Security audit log for tracking authentication events and security incidents
    """
    EVENT_TYPES = [
        ('login_success', 'Login Success'),
        ('login_failed', 'Login Failed'),
        ('password_change', 'Password Change'),
        ('account_locked', 'Account Locked'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('data_access', 'Data Access'),
        ('admin_action', 'Admin Action'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='security_logs'
    )
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Security Audit Log'
        verbose_name_plural = 'Security Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['ip_address', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.user} - {self.timestamp}"


class DataEncryptionMixin:
    """
    Mixin for encrypting sensitive data fields
    """
    
    @staticmethod
    def encrypt_field(value, key=None):
        """
        Encrypt a field value using HMAC-SHA256
        """
        if not value:
            return value
        
        if key is None:
            key = settings.SECRET_KEY.encode()
        
        # Create HMAC hash
        signature = hmac.new(key, value.encode(), hashlib.sha256).hexdigest()
        return f"encrypted:{signature}"
    
    @staticmethod
    def decrypt_field(encrypted_value, original_value, key=None):
        """
        Verify encrypted field (HMAC verification)
        """
        if not encrypted_value or not encrypted_value.startswith('encrypted:'):
            return False
        
        if key is None:
            key = settings.SECRET_KEY.encode()
        
        signature = encrypted_value.replace('encrypted:', '')
        expected_signature = hmac.new(key, original_value.encode(), hashlib.sha256).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)


class SecurityManager:
    """
    Central security manager for handling various security operations
    """
    
    def __init__(self):
        self.max_login_attempts = 5
        self.lockout_duration = 30  # minutes
        self.session_timeout = 60  # minutes
    
    def log_security_event(self, event_type, user=None, ip_address=None, user_agent=None, details=None):
        """
        Log security events for audit purposes
        """
        try:
            SecurityAuditLog.objects.create(
                user=user,
                event_type=event_type,
                ip_address=ip_address or '127.0.0.1',
                user_agent=user_agent or '',
                details=details or {}
            )
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
    
    def check_login_attempts(self, username, ip_address):
        """
        Check if user/IP has exceeded login attempts
        """
        cache_key = f"login_attempts:{username}:{ip_address}"
        attempts = cache.get(cache_key, 0)
        
        if attempts >= self.max_login_attempts:
            return False, f"Account locked due to {attempts} failed login attempts"
        
        return True, ""
    
    def record_failed_login(self, username, ip_address):
        """
        Record failed login attempt
        """
        cache_key = f"login_attempts:{username}:{ip_address}"
        attempts = cache.get(cache_key, 0) + 1
        cache.set(cache_key, attempts, timeout=self.lockout_duration * 60)
        
        if attempts >= self.max_login_attempts:
            self.log_security_event(
                'account_locked',
                ip_address=ip_address,
                details={'username': username, 'attempts': attempts}
            )
    
    def clear_login_attempts(self, username, ip_address):
        """
        Clear login attempts after successful login
        """
        cache_key = f"login_attempts:{username}:{ip_address}"
        cache.delete(cache_key)
    
    def generate_secure_token(self, length=32):
        """
        Generate cryptographically secure random token
        """
        return secrets.token_urlsafe(length)
    
    def validate_session_security(self, request):
        """
        Validate session security parameters
        """
        session = request.session
        
        # Check session timeout
        last_activity = session.get('last_activity')
        if last_activity:
            last_activity_time = datetime.fromisoformat(last_activity)
            if timezone.now() - last_activity_time > timedelta(minutes=self.session_timeout):
                return False, "Session expired"
        
        # Update last activity
        session['last_activity'] = timezone.now().isoformat()
        
        # Check IP consistency (optional, can be disabled for mobile users)
        session_ip = session.get('ip_address')
        current_ip = self.get_client_ip(request)
        
        if session_ip and session_ip != current_ip:
            # Log suspicious activity but don't block (mobile users change IPs)
            self.log_security_event(
                'suspicious_activity',
                user=request.user if request.user.is_authenticated else None,
                ip_address=current_ip,
                details={'session_ip': session_ip, 'current_ip': current_ip}
            )
        
        return True, ""
    
    def get_client_ip(self, request):
        """
        Get client IP address from request
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip
    
    def sanitize_input(self, input_data):
        """
        Sanitize user input to prevent XSS and injection attacks
        """
        if isinstance(input_data, str):
            # Basic HTML tag removal
            import re
            input_data = re.sub(r'<[^>]+>', '', input_data)
            # Remove potentially dangerous characters
            input_data = input_data.replace('<', '&lt;').replace('>', '&gt;')
            input_data = input_data.replace('"', '&quot;').replace("'", '&#x27;')
        
        return input_data
    
    def check_password_strength(self, password):
        """
        Check password strength according to security policies
        """
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        # Check against common passwords
        common_passwords = ['password', '123456', 'admin', 'user', 'test']
        if password.lower() in common_passwords:
            errors.append("Password is too common")
        
        return len(errors) == 0, errors


# Security signal handlers
@receiver(user_logged_in)
def log_successful_login(sender, request, user, **kwargs):
    """
    Log successful login attempts
    """
    security_manager = SecurityManager()
    ip_address = security_manager.get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    security_manager.log_security_event(
        'login_success',
        user=user,
        ip_address=ip_address,
        user_agent=user_agent,
        details={'login_method': 'web'}
    )
    
    # Clear any failed login attempts
    security_manager.clear_login_attempts(user.username, ip_address)
    
    # Set session security parameters
    request.session['ip_address'] = ip_address
    request.session['last_activity'] = timezone.now().isoformat()


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """
    Log failed login attempts
    """
    security_manager = SecurityManager()
    ip_address = security_manager.get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    username = credentials.get('username', 'unknown')
    
    security_manager.log_security_event(
        'login_failed',
        ip_address=ip_address,
        user_agent=user_agent,
        details={'username': username, 'reason': 'invalid_credentials'}
    )
    
    # Record failed attempt
    security_manager.record_failed_login(username, ip_address)


class SecureModelMixin(models.Model):
    """
    Mixin for models that need enhanced security features
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated'
    )
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        """
        Override save to add security logging
        """
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Log data access/modification
        security_manager = SecurityManager()
        security_manager.log_security_event(
            'data_access',
            user=self.updated_by or self.created_by,
            details={
                'model': self.__class__.__name__,
                'action': 'create' if is_new else 'update',
                'object_id': self.pk
            }
        )


def apply_security_headers(response):
    """
    Apply security headers to HTTP responses
    """
    # Prevent clickjacking
    response['X-Frame-Options'] = 'DENY'
    
    # Prevent MIME type sniffing
    response['X-Content-Type-Options'] = 'nosniff'
    
    # Enable XSS protection
    response['X-XSS-Protection'] = '1; mode=block'
    
    # Strict transport security (HTTPS only)
    response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Content security policy
    response['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' https:; "
        "connect-src 'self';"
    )
    
    # Referrer policy
    response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    return response


class SecurityMiddleware:
    """
    Custom security middleware for additional protection
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.security_manager = SecurityManager()
    
    def __call__(self, request):
        # Pre-processing
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Validate session security
            is_valid, message = self.security_manager.validate_session_security(request)
            if not is_valid:
                from django.contrib.auth import logout
                logout(request)
                from django.http import HttpResponseRedirect
                return HttpResponseRedirect('/login/?session_expired=1')
        
        response = self.get_response(request)
        
        # Post-processing - apply security headers
        response = apply_security_headers(response)
        
        return response