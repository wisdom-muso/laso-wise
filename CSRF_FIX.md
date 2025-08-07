# CSRF Verification Fix

## Issue
The admin login page was showing a CSRF verification error:

```
Forbidden (403)
CSRF verification failed. Request aborted.
```

## Root Cause
The application was missing proper CSRF configuration in the environment variables. The CSRF_TRUSTED_ORIGINS setting was not properly configured to include the domains from which requests are allowed.

## Solution
1. Created a `.env` file based on the `.env.example` template
2. Set `DEBUG=True` to get more detailed error information
3. Added the correct domains to `CSRF_TRUSTED_ORIGINS`, including:
   - https://work-1-zasdprpklhsumowf.prod-runtime.all-hands.dev
   - https://work-2-zasdprpklhsumowf.prod-runtime.all-hands.dev
   - http://localhost:12000
   - http://127.0.0.1:12000
4. Set `CSRF_COOKIE_SECURE=False` for development environment

## Port Configuration
The application is configured to run on two different ports:
- Port 12000: Django development server (configured in `.env` as `DJANGO_PORT=12000`)
- Port 8005: Docker container with Gunicorn (configured in `docker-compose.yml` and `docker-compose.prod.yml`)

In production mode, Nginx serves on port 12000 and proxies requests to the Django application running on port 8005.

## Implementation Notes
- The `.env` file is not committed to the repository for security reasons (it's in `.gitignore`)
- For deployment, make sure to create a proper `.env` file with the correct CSRF settings
- In production, set `CSRF_COOKIE_SECURE=True` and `SESSION_COOKIE_SECURE=True` if using HTTPS