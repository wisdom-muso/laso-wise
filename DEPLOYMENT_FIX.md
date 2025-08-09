# LASO-WISE Deployment Fix

## Issue Fixed: AppRegistryNotReady Error

### Problem
The application was failing to start on VPS deployment with the error:
```
django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet.
```

This error occurred because Django admin site configuration was being set too early in the application lifecycle (in `laso/urls.py` at module level), before Django had finished loading all applications.

### Root Cause
In `laso/urls.py`, lines 24-26 contained:
```python
admin.site.site_header = "Laso Digital Health Admin"
admin.site.site_title = "Laso Digital Health Admin Portal"
admin.site.index_title = "Welcome to Laso Digital Health Admin Portal"
```

This code executed when the module was imported, which happens during Django's startup process before all apps are fully loaded.

### Solution Applied
1. **Removed admin configuration from urls.py**: Eliminated the problematic admin site configuration from the URLs module.

2. **Added AppConfig with ready() method**: Created a proper AppConfig in `core/apps.py` with a `ready()` method that executes after all apps are loaded:
```python
class CoreConfig(AppConfig):
    name = "core"
    
    def ready(self):
        from django.contrib import admin
        from django.conf import settings
        
        admin.site.site_header = getattr(settings, 'ADMIN_SITE_HEADER', 'Laso Digital Health Administration')
        admin.site.site_title = getattr(settings, 'ADMIN_SITE_TITLE', 'Laso Digital Health Admin Portal')
        admin.site.index_title = getattr(settings, 'ADMIN_INDEX_TITLE', 'Welcome to Laso Digital Health Admin Portal')
```

3. **Updated INSTALLED_APPS**: Changed the core app reference in settings.py from `"core"` to `"core.apps.CoreConfig"` to ensure the custom AppConfig is used.

### Files Modified
- `laso/urls.py`: Removed admin site configuration
- `core/apps.py`: Added CoreConfig with ready() method
- `laso/settings.py`: Updated INSTALLED_APPS to use explicit AppConfig

### Verification
- `python manage.py check` passes successfully
- `python manage.py runserver` starts without errors
- Admin interface maintains proper branding

### Additional Improvements Made
- Reverted DEBUG setting to environment-based configuration for production safety
- Used `getattr()` with fallbacks for robust settings access
- Added proper documentation comments

## Deployment Instructions
1. Pull the latest changes
2. Rebuild your Docker containers if using Docker
3. The application should now start successfully on your VPS

## System Status: FIXED ✅
The AppRegistryNotReady error has been resolved and the application is ready for production deployment.