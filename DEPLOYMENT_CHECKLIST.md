# VPS Deployment Checklist for http://65.108.91.110/

## ✅ CSRF Configuration Status
Your Django application is now properly configured to avoid CSRF issues on your VPS:

### Current Settings:
- **ALLOWED_HOSTS**: Includes `65.108.91.110` ✅
- **CSRF_TRUSTED_ORIGINS**: Includes `http://65.108.91.110` and `https://65.108.91.110` ✅
- **CSRF_COOKIE_SECURE**: Set to `False` (allows HTTP) ✅
- **SESSION_COOKIE_SECURE**: Set to `False` (allows HTTP) ✅
- **SECURE_SSL_REDIRECT**: Set to `False` (no forced HTTPS) ✅

## Pre-Deployment Steps:

1. **Environment File**: 
   - Ensure `.env` file exists in your project root
   - Verify it contains the correct settings for HTTP deployment

2. **Static Files**:
   ```bash
   python manage.py collectstatic --noinput
   ```

3. **Database Migration**:
   ```bash
   python manage.py migrate
   ```

4. **Create Superuser** (if needed):
   ```bash
   python manage.py createsuperuser
   ```

## Deployment Command:
```bash
python manage.py runserver 0.0.0.0:80
```

## Testing After Deployment:

1. **Logo Loading**: Visit `http://65.108.91.110/login/` - logo should display
2. **Login Functionality**: Test login with both admin and patient accounts
3. **Form Submissions**: Ensure no CSRF errors when submitting forms
4. **Navigation**: Verify proper redirects after login

## Troubleshooting:

If you encounter CSRF errors:
1. Check that your `.env` file has `CSRF_COOKIE_SECURE=False`
2. Verify `http://65.108.91.110` is in `CSRF_TRUSTED_ORIGINS`
3. Clear browser cookies and try again

## Security Notes:
- The current configuration is optimized for HTTP deployment
- For production with HTTPS, update the security settings in `.env`
- Consider using a reverse proxy (nginx) for production deployments