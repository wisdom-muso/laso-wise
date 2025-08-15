# 🔧 Database & Admin Fix Solution

## 🚨 Issues Identified

### 1. Missing Database Tables
- **Error**: `OperationalError: no such table: core_ehrrecord`
- **Error**: `OperationalError: no such table: core_soapnote`
- **Cause**: Database migrations not applied properly

### 2. Telemedicine Admin Not Visible
- **Issue**: Telemedicine models not accessible in admin interface
- **Cause**: Models are registered but may not be visible due to navigation or migration issues

## 🛠️ Root Cause Analysis

### Database Migration Issues
1. **Migration Conflicts**: Multiple migration files with similar timestamps
2. **Incomplete Migration Application**: Some migrations may have failed silently
3. **Docker Environment**: Migrations not run in production containers

### Admin Interface Issues
1. **Model Registration**: All models are properly registered in admin.py files
2. **Navigation**: Admin interface should show Core and Telemedicine sections
3. **Permissions**: May need superuser account with proper permissions

## 🎯 Solution Implementation

### Step 1: Fix Database Tables

Run the database fix script:
```bash
./fix_database.sh
```

This script will:
- ✅ Check current migration status
- ✅ Create missing migrations if needed
- ✅ Apply all pending migrations
- ✅ Create missing database tables
- ✅ Create superuser account (admin/admin123)
- ✅ Verify table creation

### Step 2: Verify Admin Access

After running the fix script, you should be able to access:

#### 🏥 Core Medical Models
- **SOAP Notes**: http://65.108.91.110:12000/admin/core/soapnote/
- **EHR Records**: http://65.108.91.110:12000/admin/core/ehrrecord/
- **Specialities**: http://65.108.91.110:12000/admin/core/speciality/
- **Reviews**: http://65.108.91.110:12000/admin/core/review/
- **Hospital Settings**: http://65.108.91.110:12000/admin/core/hospitalsettings/

#### 🎥 Telemedicine Models
- **Consultations**: http://65.108.91.110:12000/admin/telemedicine/consultation/
- **Messages**: http://65.108.91.110:12000/admin/telemedicine/consultationmessage/
- **Participants**: http://65.108.91.110:12000/admin/telemedicine/consultationparticipant/
- **Recordings**: http://65.108.91.110:12000/admin/telemedicine/consultationrecording/
- **Waiting Room**: http://65.108.91.110:12000/admin/telemedicine/waitingroom/
- **Technical Issues**: http://65.108.91.110:12000/admin/telemedicine/technicalissue/
- **Video Config**: http://65.108.91.110:12000/admin/telemedicine/videoproviderconfig/

### Step 3: Admin Credentials

**Default Login Credentials:**
- Username: `admin`
- Password: `admin123`

⚠️ **Important**: Change these credentials in production!

## 🔍 Manual Verification Steps

### 1. Check Container Status
```bash
./run.sh status
```

### 2. Check Database Tables
```bash
# Run inside Docker container
docker exec -it <container_name> python manage.py dbshell
.tables
```

You should see tables like:
- `core_soapnote`
- `core_ehrrecord`
- `telemedicine_consultation`
- `telemedicine_consultationmessage`

### 3. Verify Migrations
```bash
# Run inside Docker container
docker exec -it <container_name> python manage.py showmigrations
```

All migrations should show `[X]` (applied).

### 4. Test Admin Access
1. Go to: http://65.108.91.110:12000/admin/
2. Login with: admin / admin123
3. You should see sections for:
   - **Accounts**
   - **Bookings**
   - **Core** ← Should contain SOAP Notes, EHR Records
   - **Doctors**
   - **Patients**
   - **Telemedicine** ← Should contain Consultations, etc.
   - **Vitals**

## 📋 Expected Admin Interface Structure

### Core Section
```
📁 CORE
├── 📝 SOAP Notes
├── 🏥 EHR Records
├── ⭐ Reviews
├── 🎯 Specialities
├── 🏢 Hospital Settings
└── 📊 Audit Logs
```

### Telemedicine Section
```
📁 TELEMEDICINE
├── 📞 Consultations
├── 💬 Consultation Messages
├── 👥 Consultation Participants
├── 📹 Consultation Recordings
├── ⏳ Waiting Rooms
├── 🛠️ Technical Issues
└── ⚙️ Video Provider Configs
```

## 🚨 Troubleshooting

### If Tables Are Still Missing

1. **Check Docker Container**:
   ```bash
   docker ps
   docker exec -it <web_container> bash
   python manage.py migrate --run-syncdb
   ```

2. **Force Migration Reset** (⚠️ Use with caution):
   ```bash
   # Backup database first!
   cp db.sqlite3 db.sqlite3.backup
   
   # Reset migrations
   python manage.py migrate core zero
   python manage.py migrate telemedicine zero
   python manage.py migrate
   ```

3. **Check Migration Files**:
   ```bash
   ls -la core/migrations/
   ls -la telemedicine/migrations/
   ```

### If Admin Models Not Visible

1. **Check Model Registration**:
   - Verify `core/admin.py` imports and registrations
   - Verify `telemedicine/admin.py` imports and registrations

2. **Check App Installation**:
   - Ensure `core` and `telemedicine` are in `INSTALLED_APPS`
   - Restart containers after changes

3. **Clear Cache**:
   ```bash
   # Clear browser cache
   # Restart Django container
   ./run.sh restart
   ```

### If Permission Denied

1. **Check User Permissions**:
   ```bash
   # In Django shell
   python manage.py shell
   >>> from accounts.models import User
   >>> admin = User.objects.get(username='admin')
   >>> admin.is_superuser = True
   >>> admin.is_staff = True
   >>> admin.save()
   ```

## 📱 Quick Access Commands

### One-Command Fix
```bash
# Run this to fix everything
./fix_database.sh && echo "✅ Database fixed! Access admin at: http://65.108.91.110:12000/admin/"
```

### Check Status
```bash
./run.sh status
```

### View Logs
```bash
./run.sh logs web
```

### Restart Services
```bash
./run.sh restart
```

## 🎯 Success Indicators

After running the fixes, you should see:

✅ **Database Tables Created**
- No more "no such table" errors
- SOAP Notes and EHR Records pages load

✅ **Admin Navigation**
- Core section with 6 models
- Telemedicine section with 7 models
- All links work without errors

✅ **Functional Features**
- Can create SOAP notes
- Can view EHR records
- Can manage consultations
- Can configure video providers

## 📞 Support

If issues persist:
1. Check logs: `./run.sh logs`
2. Verify container status: `./run.sh status`
3. Check database file: `ls -la db.sqlite3`
4. Review migration status in container

The fix script (`fix_database.sh`) handles most common issues automatically and provides detailed output for troubleshooting.