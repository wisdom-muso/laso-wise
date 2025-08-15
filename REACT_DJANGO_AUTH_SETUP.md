# React-Django Authentication & Connection Setup

## Overview

This document describes the robust authentication system between the React frontend and Django backend, including connection resilience, error handling, and security measures.

## Architecture

### Backend (Django)
- **Authentication Method**: Django REST Framework Token Authentication
- **CORS Configuration**: Properly configured for React frontend ports
- **API Endpoints**: RESTful endpoints under `/accounts/api/`
- **Security**: CSRF protection, secure cookies, token-based auth

### Frontend (React)
- **HTTP Client**: Axios with custom interceptors
- **Token Storage**: localStorage with validation
- **Connection Monitoring**: Real-time health checks
- **Error Handling**: Comprehensive retry logic and user feedback

## Key Features

### 1. Robust Connection Handling

#### Automatic Retry Logic
```typescript
// Configurable retry for failed requests
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

// Retries on network errors or 5xx server errors
if (!error.response || error.response.status >= 500) {
  await delay(RETRY_DELAY * retryCount);
  return api(config);
}
```

#### Connection Health Monitoring
```typescript
// Real-time connection status tracking
const { isOnline, isApiHealthy, latency } = useConnectionStatus();

// Periodic health checks
const healthCheck = async (): Promise<boolean> => {
  // Tests API availability without authentication
}
```

### 2. Enhanced Authentication Flow

#### Token Management
- **Format**: Django REST Framework Token (`Token <token>`)
- **Storage**: localStorage with validation
- **Lifecycle**: Auto-creation, validation, refresh, cleanup

#### Authentication Process
1. **Login**: POST to `/accounts/api/login/` with email/password
2. **Token Storage**: Store returned token in localStorage
3. **Request Headers**: Automatic `Authorization: Token <token>` header
4. **Validation**: Periodic token validation with `/accounts/api/me/`
5. **Logout**: POST to `/accounts/api/logout/` with token cleanup

### 3. Error Handling & User Experience

#### Comprehensive Error Types
- **401 Unauthorized**: Auto-redirect to login, token cleanup
- **403 Forbidden**: Permission denied messages
- **404 Not Found**: Resource not found logging
- **5xx Server Errors**: Automatic retry with exponential backoff
- **Network Errors**: Connection status updates and retry

#### User-Friendly Messages
```typescript
// Context-aware error messages
if (error.response?.status === 401) {
  message = 'Invalid email or password';
} else if (error.code === 'NETWORK_ERROR') {
  message = 'Network error. Please check your connection.';
}
```

## Configuration Files

### 1. API Configuration (`frontend/src/lib/api.ts`)

```typescript
// Base configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE || 'http://65.108.91.110:12000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});
```

### 2. Django Settings (`laso/settings.py`)

```python
# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://65.108.91.110:3000",  # React frontend
    "http://65.108.91.110:12000", # Nginx proxy
    "http://65.108.91.110:8005",  # Django direct
]

# REST Framework Authentication
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

### 3. Environment Variables

#### Production (`.env.prod`)
```bash
VITE_API_BASE=http://65.108.91.110:12000
HTTP_PORT=12000
CORS_ALLOWED_ORIGINS=http://65.108.91.110:3000,http://65.108.91.110:12000
```

#### Development (`.env.dev`)
```bash
VITE_API_BASE=http://65.108.91.110:8005
CORS_ALLOWED_ORIGINS=http://65.108.91.110:3000,http://localhost:3000
```

## API Endpoints

### Authentication Endpoints
- `POST /accounts/api/login/` - User login
- `POST /accounts/api/logout/` - User logout
- `POST /accounts/api/register/` - User registration
- `GET /accounts/api/me/` - Get current user profile
- `PUT /accounts/api/me/update/` - Update user profile

### Data Endpoints
- `GET /doctors/api/` - List doctors
- `GET /patients/api/` - List patients
- `GET /vitals/api/records/` - Vital records
- `GET /bookings/api/appointments/` - Appointments
- `GET /telemedicine/api/consultations/` - Consultations

## Security Measures

### 1. CSRF Protection
- CSRF tokens automatically included in requests
- Meta tag reading for token extraction
- Proper CORS configuration

### 2. Token Security
- Tokens stored securely in localStorage
- Automatic cleanup on logout/401 errors
- Token validation before API calls

### 3. Request Security
- HTTPS-ready configuration
- Secure cookie settings in production
- Proper CORS origin validation

## Testing & Validation

### 1. API Test Suite (`frontend/src/lib/api-test.ts`)

```typescript
// Run comprehensive tests
import { apiTest } from './lib/api-test';

// Basic connectivity
await apiTest.runBasicConnectivityTests();

// Authentication flow
await apiTest.runAuthenticationTests(email, password);

// Full test suite
await apiTest.runFullTestSuite();
```

### 2. Browser Console Testing
```javascript
// Available in browser console
window.testAPI.runFullTestSuite();
window.quickTest(); // Shorthand
```

### 3. Connection Monitoring
```typescript
// Real-time connection status
const { isOnline, isApiHealthy, latency, lastChecked } = useConnectionStatus();

// Manual connection check
const checkConnection = () => testConnection();
```

## Troubleshooting

### Common Issues

#### 1. CORS Errors
- **Symptom**: "Access to fetch at ... has been blocked by CORS policy"
- **Solution**: Verify CORS_ALLOWED_ORIGINS includes frontend URL
- **Check**: Django settings.py CORS configuration

#### 2. Authentication Failures
- **Symptom**: 401 errors on authenticated endpoints
- **Solution**: Check token format (`Token <token>` not `Bearer <token>`)
- **Check**: localStorage token storage

#### 3. Connection Timeouts
- **Symptom**: Network timeout errors
- **Solution**: Verify backend is running on correct port
- **Check**: VITE_API_BASE environment variable

#### 4. Library Folder Missing
- **Symptom**: Import errors for `../lib/api`
- **Solution**: Fixed in `.gitignore` - no longer ignores frontend lib folders
- **Check**: Ensure `/workspace/frontend/src/lib/api.ts` exists

### Debug Commands

```bash
# Check backend health
curl http://65.108.91.110:12000/admin/

# Test CORS
curl -H "Origin: http://65.108.91.110:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS \
     http://65.108.91.110:12000/accounts/api/login/

# Test authentication
curl -X POST http://65.108.91.110:12000/accounts/api/login/ \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"password"}'
```

## Performance & Reliability

### Connection Resilience
- **Retry Logic**: 3 retries with exponential backoff
- **Health Checks**: Every 30 seconds when online
- **Timeout Handling**: 30-second timeout with graceful degradation
- **Network Detection**: Online/offline event handling

### Caching Strategy
- **Token Persistence**: localStorage with validation
- **User Data**: Memory cache with refresh capability
- **Connection Status**: Real-time monitoring

### Error Recovery
- **Automatic Retry**: For network and server errors
- **Token Refresh**: Validation and cleanup on failures
- **User Feedback**: Clear error messages and loading states

## Maintenance

### Regular Checks
1. **Token Validation**: Ensure tokens are properly formatted
2. **CORS Origins**: Update allowed origins for new deployments
3. **Error Logs**: Monitor console for authentication issues
4. **Connection Health**: Check health check success rates

### Updates & Migrations
1. **Environment Variables**: Update VITE_API_BASE for new deployments
2. **CORS Configuration**: Add new origins as needed
3. **API Endpoints**: Update endpoints structure if backend changes
4. **Authentication Method**: Prepared for JWT or other auth methods

This setup provides a robust, scalable, and maintainable authentication system between React and Django with comprehensive error handling and connection resilience.