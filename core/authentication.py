"""
Custom authentication backends for Laso Healthcare System
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Custom authentication backend that allows users to login with either
    their username or email address.
    
    This backend provides enhanced security by supporting multiple login methods
    while maintaining the same password validation.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user with either username or email
        
        Args:
            request: HTTP request object
            username: Username or email address
            password: User password
            **kwargs: Additional keyword arguments
            
        Returns:
            User object if authentication successful, None otherwise
        """
        if username is None or password is None:
            return None
        
        try:
            # Try to find user by username or email
            user = User.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
            
            # Check if the password is correct
            if user.check_password(password):
                return user
                
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user
            User().set_password(password)
            return None
        
        return None
    
    def get_user(self, user_id):
        """
        Get user by ID
        
        Args:
            user_id: User ID
            
        Returns:
            User object if found, None otherwise
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class SecureAuthenticationBackend(EmailOrUsernameModelBackend):
    """
    Enhanced authentication backend with additional security features
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Enhanced authentication with security logging
        """
        # Log authentication attempt (for security monitoring)
        if request:
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # You can add logging here for security monitoring
            # logger.info(f"Authentication attempt from {ip_address} for {username}")
        
        # Call parent authentication method
        user = super().authenticate(request, username, password, **kwargs)
        
        if user:
            # Additional security checks can be added here
            # For example: check if account is locked, check login attempts, etc.
            
            # Update last login IP (if you have this field)
            if request and hasattr(user, 'last_login_ip'):
                user.last_login_ip = self.get_client_ip(request)
                user.save(update_fields=['last_login_ip'])
        
        return user
    
    def get_client_ip(self, request):
        """
        Get client IP address from request
        
        Args:
            request: HTTP request object
            
        Returns:
            Client IP address as string
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip