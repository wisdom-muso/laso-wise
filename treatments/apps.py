from django.apps import AppConfig


class TreatmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'treatments'
    
    def ready(self):
        """Import signals when the app is ready"""
        try:
            import treatments.signals_vitals
        except ImportError:
            pass
