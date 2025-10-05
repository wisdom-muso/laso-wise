# VPS Login Issue Fix

## Problem Description

When deploying the Laso Healthcare System on a VPS and accessing it via HTTP (e.g., `http://65.108.91.110`), users experience a login redirect loop where:

1. User enters credentials on login page
2. URL changes to `http://65.108.91.110/login/?next=/dashboard/`
3. User remains on the login screen instead of being redirected to dashboard

## Root Cause

The issue was caused by Django security settings that were configured for HTTPS environments but being used in an HTTP deployment:

- `SESSION_COOKIE_SECURE = True` - Prevents session cookies from being sent over HTTP
- `CSRF_COOKIE_SECURE = True` - Prevents CSRF cookies from being sent over HTTP
- `SECURE_SSL_REDIRECT = True` - Attempts to redirect HTTP to HTTPS

When these settings are enabled in an HTTP environment, the browser cannot store session cookies, causing authentication to fail silently.

## Solution

### 1. Modified Django Settings

Updated `/laso/settings.py` to conditionally apply security settings based on whether HTTPS is being used:

```python
# Check if we're using HTTPS (via environment variable)
USE_HTTPS = config('USE_HTTPS', default=False, cast=bool)

if not DEBUG:
    # Basic security settings (always applied)
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    
    # HTTPS-specific settings (conditional)
    if USE_HTTPS:
        SECURE_HSTS_INCLUDE_SUBDOMAINS = True
        SECURE_HSTS_PRELOAD = True
        SECURE_HSTS_SECONDS = 31536000
        SECURE_SSL_REDIRECT = True
        SESSION_COOKIE_SECURE = True
        CSRF_COOKIE_SECURE = True
    else:
        # HTTP deployment settings
        SESSION_COOKIE_SECURE = False
        CSRF_COOKIE_SECURE = False
        SECURE_SSL_REDIRECT = False
```

### 2. Improved Cookie Settings

- Changed `SESSION_COOKIE_SAMESITE` and `CSRF_COOKIE_SAMESITE` from `'Strict'` to `'Lax'` for better compatibility
- Made secure cookie settings conditional based on HTTPS usage

### 3. Environment Configuration

Created `.env.production.example` template with proper settings for HTTP deployment:

```bash
DEBUG=False
USE_HTTPS=False
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,65.108.91.110,your-domain.com
```

## Deployment Instructions

### Quick Fix (Automated)

1. Run the automated fix script:
   ```bash
   ./fix-vps-login.sh
   ```

### Manual Fix

1. **Create/Update Environment File:**
   ```bash
   cp .env.production.example .env
   ```

2. **Edit `.env` file with your settings:**
   ```bash
   DEBUG=False
   USE_HTTPS=False
   SECRET_KEY=your-actual-secret-key
   POSTGRES_PASSWORD=your-database-password
   REDIS_PASSWORD=your-redis-password
   ```

3. **Rebuild and Deploy:**
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

4. **Run Migrations:**
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py collectstatic --noinput
   ```

5. **Create Admin User (if needed):**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

## Verification

After applying the fix:

1. Navigate to `http://65.108.91.110`
2. Try logging in with valid credentials
3. You should be successfully redirected to the dashboard
4. Check that session cookies are being set in browser developer tools

## Security Considerations

### For HTTP Deployment (Current Fix)
- Session cookies are not encrypted in transit
- CSRF protection is still active but cookies are not secure
- Suitable for internal networks or development environments

### For Production HTTPS Deployment
To enable HTTPS security features:

1. Set up SSL certificate
2. Configure nginx for HTTPS
3. Update environment: `USE_HTTPS=True`
4. Update `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` with HTTPS URLs

## Troubleshooting

### If login still fails:

1. **Check Docker logs:**
   ```bash
   docker-compose logs web
   docker-compose logs nginx
   ```

2. **Verify environment variables:**
   ```bash
   docker-compose exec web python manage.py shell -c "
   from django.conf import settings
   print('DEBUG:', settings.DEBUG)
   print('SESSION_COOKIE_SECURE:', settings.SESSION_COOKIE_SECURE)
   print('CSRF_COOKIE_SECURE:', settings.CSRF_COOKIE_SECURE)
   "
   ```

3. **Check database connectivity:**
   ```bash
   docker-compose exec web python manage.py dbshell
   ```

4. **Clear browser cache and cookies**

### Common Issues:

- **Database not ready:** Wait longer for PostgreSQL to initialize
- **Static files not loading:** Run `collectstatic` command
- **Permission errors:** Check Docker volume permissions

## Files Modified

- `/laso/settings.py` - Updated security settings to be conditional
- `.env.production.example` - Created environment template
- `fix-vps-login.sh` - Created automated fix script
- `VPS_LOGIN_FIX.md` - This documentation file

## Future Improvements

1. **SSL/HTTPS Setup:** Configure proper SSL certificates for production
2. **Domain Configuration:** Set up proper domain name instead of IP
3. **Security Hardening:** Implement additional security measures for production
4. **Monitoring:** Add logging and monitoring for authentication events