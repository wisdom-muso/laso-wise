from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SyncMonitorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sync_monitor'
    verbose_name = _('Sync & System Monitoring')

    def ready(self):
        import sync_monitor.signals