"""
Login Session Tracking Models for Laso Healthcare
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class LoginSession(models.Model):
    """
    Model to track user login sessions
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='login_sessions',
        verbose_name=_('User')
    )
    
    login_time = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Login Time')
    )
    
    logout_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Logout Time')
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('IP Address')
    )
    
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('User Agent')
    )
    
    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        verbose_name=_('Session Key')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )
    
    class Meta:
        verbose_name = _('Login Session')
        verbose_name_plural = _('Login Sessions')
        ordering = ['-login_time']
        indexes = [
            models.Index(fields=['user', '-login_time']),
            models.Index(fields=['is_active', '-login_time']),
            models.Index(fields=['ip_address', '-login_time']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.login_time.strftime('%Y-%m-%d %H:%M:%S')}"
    
    @property
    def duration(self):
        """Calculate session duration"""
        if self.logout_time:
            return self.logout_time - self.login_time
        elif self.is_active:
            return timezone.now() - self.login_time
        return None
    
    @property
    def duration_display(self):
        """Human readable duration"""
        duration = self.duration
        if not duration:
            return _('Unknown')
        
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def end_session(self):
        """Mark session as ended"""
        self.logout_time = timezone.now()
        self.is_active = False
        self.save(update_fields=['logout_time', 'is_active', 'updated_at'])