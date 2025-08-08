from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class VitalsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vitals'
    verbose_name = _('Vitals Tracking')
    
    def ready(self):
        # Import signals
        import vitals.signals