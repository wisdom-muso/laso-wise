# 🔧 Frontend White Screen Fix Guide

## Problem
The React frontend at `http://65.108.91.110:3000` shows a white screen instead of the application.

## Root Cause
The React frontend was configured to connect to `localhost:8005` which doesn't work on a remote server. It needs to connect to `65.108.91.110:12000` where the Django backend is actually running.

## ✅ Changes Made

### 1. Updated Docker Compose Configuration
**File: `docker-compose.yml`**
- Changed backend port mapping from `8005:8005` to `12000:8005` 
- Updated frontend API base URL from `http://localhost:8005` to `http://65.108.91.110:12000`
- Updated CSRF trusted origins to include port 12000

### 2. Updated Frontend Environment
**File: `frontend/.env`**
```bash
# Before
VITE_API_BASE=http://localhost:8005

# After  
VITE_API_BASE=http://65.108.91.110:12000
```

### 3. Updated API Configuration
**File: `frontend/src/lib/api.ts`**
- Changed default API URL from `localhost:8005` to `65.108.91.110:12000`
- Updated WebSocket URL to use the correct server address

### 4. Updated Run Script
**File: `run.sh`**
- Updated status messages to show correct URLs:
  - Backend: `http://65.108.91.110:12000`
  - Frontend: `http://65.108.91.110:3000`

## 🚀 Steps to Fix

### 1. Stop Current Services
```bash
./run.sh stop
```

### 2. Restart with Updated Configuration
```bash
./run.sh dev
```

### 3. Verify Services
After restart, you should see:
- ✅ **Bootstrap Frontend**: `http://65.108.91.110:12000/` (working)
- ✅ **Django Admin**: `http://65.108.91.110:12000/admin` (working)
- ✅ **React Frontend**: `http://65.108.91.110:3000` (should now work)
- ✅ **API Endpoints**: `http://65.108.91.110:12000/api/` (accessible)

## 🔍 Troubleshooting

### If React Frontend Still Shows White Screen:

1. **Check Browser Console** (F12 → Console):
   - Look for network errors
   - Check if API calls are reaching `65.108.91.110:12000`
   - Look for CORS errors

2. **Check Container Logs**:
   ```bash
   docker logs <frontend-container-name>
   ```

3. **Verify API Connection**:
   - Test: `http://65.108.91.110:12000/accounts/profile/`
   - Should return JSON response or login redirect

4. **Check Network Configuration**:
   - Ensure port 3000 is open on the server
   - Verify Docker containers are running on correct ports

### Common Issues:

1. **CORS Errors**: 
   - Check Django `CORS_ALLOWED_ORIGINS` settings
   - Verify `CSRF_TRUSTED_ORIGINS` includes the frontend URL

2. **Network Connectivity**:
   - Test API endpoint directly: `curl http://65.108.91.110:12000/api/`
   - Verify firewall isn't blocking port 3000

3. **Build Issues**:
   - Check if frontend built successfully
   - Look for TypeScript or dependency errors

## 📋 Verification Checklist

After running `./run.sh dev`, verify:

- [ ] Django backend responds at `http://65.108.91.110:12000/`
- [ ] Django admin works at `http://65.108.91.110:12000/admin`  
- [ ] React frontend loads at `http://65.108.91.110:3000`
- [ ] API calls from React reach Django backend
- [ ] No CORS errors in browser console
- [ ] WebSocket connections work for real-time features

## 🎯 Expected Result

Both frontends should work simultaneously:
- **Bootstrap Frontend**: `http://65.108.91.110:12000/` (existing Django templates)
- **React Frontend**: `http://65.108.91.110:3000/` (modern telemedicine interface)

The React frontend provides the enhanced telemedicine features while the Bootstrap frontend continues to work for other functionality.