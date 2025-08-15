# Frontend-Backend Connection Fix Summary

## Problem Identified

The React frontend was showing a white screen when accessed at `http://65.108.91.110:3000` due to several configuration issues:

1. **Missing API Configuration**: The React frontend was importing from `../lib/api` but the file didn't exist
2. **Port Mismatch**: The backend was running on port 12000 in production but the code referenced port 8005
3. **Inconsistent Environment Variables**: Different files used different port configurations

## Root Cause Analysis

- The bootstrap frontend (Django templates) works because it uses Django's URL routing system (`{% url "vitals:add-vital" %}`) and doesn't need to specify external API endpoints
- The React frontend is a separate application that needs to make HTTP requests to the Django backend API
- The production environment runs nginx on port 12000 which proxies to Django on port 8005
- The React frontend needed to connect to the nginx proxy (port 12000), not directly to Django (port 8005)

## Solutions Implemented

### 1. Created Missing API Configuration (`frontend/src/lib/api.ts`)
- Added axios configuration with proper base URL
- Implemented request/response interceptors for authentication
- Defined all API endpoints used by the React components
- Added WebSocket URL helper for real-time features

### 2. Fixed Port Configuration
- Updated `docker-compose.prod.yml`: Changed HTTP_PORT default from 8005 to 12000
- Updated `docker-compose.yml`: Fixed VITE_API_BASE environment variable
- Created `.env.prod` and `.env.dev` files with correct port configurations

### 3. Updated Environment Variables
- Set `VITE_API_BASE=http://65.108.91.110:12000` for production
- Set `VITE_API_BASE=http://65.108.91.110:8005` for development
- Updated all Vite configuration files to use dynamic proxy targets

### 4. Updated Documentation
- Fixed README.md to show correct URLs
- Updated run.sh script to display correct access URLs
- Updated env.template with proper default values

## Files Modified

1. **frontend/src/lib/api.ts** (NEW) - Complete API configuration
2. **docker-compose.prod.yml** - Fixed HTTP_PORT default
3. **docker-compose.yml** - Fixed VITE_API_BASE environment variable  
4. **frontend/vite.config.ts/.js** - Dynamic proxy targets
5. **env.template** - Added VITE_API_BASE and fixed HTTP_PORT
6. **.env.prod** (NEW) - Production environment configuration
7. **.env.dev** (NEW) - Development environment configuration
8. **frontend/env.example** - Updated API base URL
9. **README.md** - Updated URLs to reflect 65.108.91.110
10. **run.sh** - Updated displayed URLs

## Expected Results

After these fixes:

1. **Bootstrap Frontend**: `http://65.108.91.110:12000/` - Will continue to work (no changes needed)
2. **Admin Dashboard**: `http://65.108.91.110:12000/admin` - Will continue to work (no changes needed)  
3. **React Frontend**: `http://65.108.91.110:3000` - Will now work correctly and connect to the backend API

## Testing Steps

1. Run `./run.sh prod` to start in production mode
2. Access `http://65.108.91.110:12000/` - Should show bootstrap frontend
3. Access `http://65.108.91.110:12000/admin` - Should show admin dashboard
4. Access `http://65.108.91.110:3000` - Should now show React frontend instead of white screen

## Technical Details

The key insight was understanding that:
- Bootstrap templates work because they're server-side rendered by Django
- React frontend needs to make client-side HTTP requests to Django's API endpoints
- In production, nginx acts as a reverse proxy on port 12000
- The React frontend should connect to the nginx proxy, not directly to Django

This fix ensures both frontends work correctly with the same backend infrastructure.