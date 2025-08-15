# 🚀 Complete LASO System Setup & Troubleshooting Guide

## 📋 Overview

This guide provides step-by-step instructions to properly run the LASO Digital Health system and fix the React frontend white screen issue.

## ⚠️ Current Issue Summary

**Problem**: React frontend on port 3000 shows white screen
**Root Causes**: 
- Missing .env.dev file (warning in logs)
- Frontend API configuration pointing to wrong port
- Build process issues in Docker container
- Missing error boundary for debugging

## 🔧 Pre-Setup Requirements

### System Requirements
- Docker and Docker Compose installed
- Minimum 4GB RAM
- Port 3000, 8005, and 12000 available

### Verify Docker Installation
```bash
docker --version
docker-compose --version
```

## 🎯 Step-by-Step Fix and Setup

### Step 1: Apply All Fixes (CRITICAL)

First, you need to pull the latest fixes from the repository:

```bash
# Make sure you're in the project directory
cd ~/laso-wise

# Pull latest changes with fixes
git pull origin cursor/fix-frontend-backend-connection-and-port-mismatch-a173

# Alternatively, if using master branch:
git pull origin master
```

### Step 2: Run Database Fixes

```bash
# Fix database migrations and admin issues
./fix_database.sh
```

This will:
- ✅ Create missing database tables
- ✅ Apply Django migrations
- ✅ Create superuser (admin/admin123)
- ✅ Fix SOAP Notes and EHR Records

### Step 3: Stop All Running Containers

```bash
# Stop all running containers
docker-compose down

# Remove containers if needed
docker-compose down --volumes --remove-orphans
```

### Step 4: Verify File Structure

```bash
# Check critical files exist
./debug_frontend.sh files
```

Expected output should show all files exist:
- ✅ frontend/package.json exists
- ✅ frontend/index.html exists  
- ✅ frontend/src/main.tsx exists
- ✅ frontend/src/lib/api.ts exists
- ✅ frontend/vite.config.ts exists
- ✅ frontend/.env exists

### Step 5: Start the System

```bash
# Start the complete system
./run.sh
```

**Expected Output:**
```
[SUCCESS] Application started in development mode!
[INFO] Backend API: http://65.108.91.110:8005
[INFO] Frontend: http://65.108.91.110:3000
```

### Step 6: Verify Services Are Running

```bash
# Check container status
docker ps

# You should see:
# - laso-dev-web-1 (backend on port 12000->8005)
# - laso-dev-frontend-1 (frontend on port 3000)
```

### Step 7: Debug Frontend If Still White Screen

```bash
# Run comprehensive frontend debugging
./debug_frontend.sh

# Or check specific issues:
./debug_frontend.sh logs     # Check container logs
./debug_frontend.sh env      # Check environment variables
./debug_frontend.sh diag     # Run full diagnostics
```

### Step 8: Test All Services

1. **Backend Django**: http://65.108.91.110:12000
2. **Admin Panel**: http://65.108.91.110:12000/admin/ (admin/admin123)
3. **React Frontend**: http://65.108.91.110:3000

## 🌐 Access URLs and Credentials

### Service URLs
| Service | URL | Purpose |
|---------|-----|---------|
| Backend (Bootstrap) | http://65.108.91.110:12000 | Django templates |
| Admin Panel | http://65.108.91.110:12000/admin/ | Django admin |
| React Frontend | http://65.108.91.110:3000 | React SPA |

### Default Credentials
- **Username**: admin
- **Password**: admin123
- **Note**: Change in production!

## 🚨 Troubleshooting Common Issues

### Issue 1: Frontend White Screen

**Symptoms:**
- Port 3000 accessible but shows white screen
- No console errors visible
- Container appears to be running

**Solutions:**
```bash
# Method 1: Rebuild frontend container
./debug_frontend.sh rebuild

# Method 2: Check container logs
docker logs laso-dev-frontend-1

# Method 3: Access container shell for manual debugging
docker exec -it laso-dev-frontend-1 sh
cd /usr/src/app/frontend
npm run dev
```

### Issue 2: Missing .env.dev Warning

**Symptoms:**
- `[WARNING] Environment file .env.dev not found`

**Solution:**
```bash
# The .env.dev file should now exist with correct content
cat .env.dev

# If missing, create it:
cat > .env.dev << EOF
DEBUG=True
VITE_API_BASE=http://65.108.91.110:12000
FRONTEND_API_BASE=http://65.108.91.110:12000
NODE_ENV=development
EOF
```

### Issue 3: API Connection Issues

**Symptoms:**
- Frontend loads but can't connect to backend
- 404 or CORS errors in browser console

**Solutions:**
```bash
# Check if backend is accessible
curl http://65.108.91.110:12000

# Check API endpoint
curl http://65.108.91.110:12000/admin/

# Verify CORS settings in Django
docker exec -it laso-dev-web-1 python manage.py shell
```

### Issue 4: Database Table Missing

**Symptoms:**
- `OperationalError: no such table: core_ehrrecord`
- Admin panel showing errors

**Solution:**
```bash
# Run database fix script
./fix_database.sh

# If still issues, run manual migration
docker exec -it laso-dev-web-1 python manage.py migrate
```

### Issue 5: Port Conflicts

**Symptoms:**
- Containers fail to start
- Port already in use errors

**Solutions:**
```bash
# Check what's using ports
sudo netstat -tlnp | grep -E "(3000|8005|12000)"

# Kill processes using the ports
sudo kill $(sudo lsof -t -i:3000)
sudo kill $(sudo lsof -t -i:12000)

# Restart containers
./run.sh
```

## 🔍 Manual Debugging Steps

### Frontend Debugging

1. **Check Container Logs:**
   ```bash
   docker logs laso-dev-frontend-1 --tail 50
   ```

2. **Access Container Shell:**
   ```bash
   docker exec -it laso-dev-frontend-1 sh
   ```

3. **Check Process Status:**
   ```bash
   docker exec laso-dev-frontend-1 ps aux
   ```

4. **Test Direct Build:**
   ```bash
   docker exec -it laso-dev-frontend-1 sh
   cd /usr/src/app/frontend
   npm install
   npm run build
   npm run preview -- --host 0.0.0.0 --port 3000
   ```

### Backend Debugging

1. **Check Django Status:**
   ```bash
   docker logs laso-dev-web-1 --tail 50
   ```

2. **Access Django Shell:**
   ```bash
   docker exec -it laso-dev-web-1 python manage.py shell
   ```

3. **Check Database:**
   ```bash
   docker exec -it laso-dev-web-1 python manage.py dbshell
   .tables
   ```

## 📊 Expected System Behavior

After successful setup:

### ✅ Backend (Port 12000)
- Shows Django bootstrap interface
- Admin panel accessible
- API endpoints respond correctly

### ✅ Frontend (Port 3000)  
- Shows React application interface
- No white screen
- Console shows successful API connection
- User can navigate between pages

### ✅ Integration
- Frontend can call backend APIs
- Authentication works between systems
- Data flows correctly

## 🔄 Complete Reset Instructions

If everything fails, do a complete reset:

```bash
# 1. Stop everything
docker-compose down --volumes --remove-orphans

# 2. Remove all containers and images
docker system prune -a

# 3. Remove database
rm -f db.sqlite3

# 4. Pull latest code
git pull origin master

# 5. Run database setup
./fix_database.sh

# 6. Start fresh
./run.sh

# 7. Check frontend
./debug_frontend.sh
```

## 🎯 Success Verification Checklist

- [ ] Backend responds at http://65.108.91.110:12000
- [ ] Admin panel works at http://65.108.91.110:12000/admin/
- [ ] Frontend shows content (not white) at http://65.108.91.110:3000
- [ ] No console errors in browser
- [ ] Can login with admin/admin123
- [ ] SOAP Notes and EHR Records accessible in admin
- [ ] Telemedicine section visible in admin

## 📞 Quick Command Reference

```bash
# Start system
./run.sh

# Debug database
./fix_database.sh

# Debug frontend
./debug_frontend.sh

# Check status
docker ps

# View logs
docker logs laso-dev-frontend-1
docker logs laso-dev-web-1

# Restart
docker-compose restart

# Complete rebuild
docker-compose up --build -d
```

## 🎉 Final Notes

The fixes include:
- ✅ Error boundary for React debugging
- ✅ Proper environment variable configuration
- ✅ Fixed API endpoint configuration
- ✅ Database migration fixes
- ✅ Comprehensive debugging tools

Follow this guide step by step, and the white screen issue should be resolved!