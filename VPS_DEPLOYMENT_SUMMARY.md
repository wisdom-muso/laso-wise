# LASO Healthcare System - VPS Deployment Summary

## 🎯 Quick Solution for Your Admin Login Issue

Your admin login issue is likely due to missing database migrations or no admin user being created. Here are the solutions:

### Option 1: Complete VPS Setup (Recommended)

If you're setting up a fresh VPS or want a complete automated setup:

```bash
# 1. Connect to your VPS
ssh root@your-vps-ip

# 2. Clone your repository
git clone https://github.com/davidgotlaso/laso-wise.git
cd laso-wise

# 3. Run the complete setup script
sudo ./vps-setup-guide.sh
```

### Option 2: Just Run Migrations (If system is partially set up)

If you already have the system installed but need to run migrations:

```bash
# Navigate to your project directory
cd /path/to/your/laso-wise

# Run migrations and create admin user
./run-migrations.sh
```

### Option 3: Manual Migration Commands

If you prefer to run commands manually:

```bash
# Activate your virtual environment
source venv/bin/activate

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

## 📋 What I've Created for You

### 1. Complete VPS Setup Script (`vps-setup-guide.sh`)
- ✅ Installs all system dependencies (Python, PostgreSQL, Redis, Nginx)
- ✅ Configures PostgreSQL database with secure credentials
- ✅ Sets up Django application with virtual environment
- ✅ Runs all database migrations
- ✅ Creates admin superuser automatically
- ✅ Configures Gunicorn and Nginx for production
- ✅ Sets up firewall and security

### 2. Migration-Only Script (`run-migrations.sh`)
- ✅ Runs Django migrations
- ✅ Creates admin user with random password
- ✅ Collects static files
- ✅ Works with existing setups
- ✅ Can start development server

### 3. Comprehensive Documentation
- ✅ `QUICK_VPS_SETUP.md` - Step-by-step guide
- ✅ `VPS_DEPLOYMENT_GUIDE.md` - Complete production guide
- ✅ This summary document

## 🔐 Admin Access Information

After running either script, you'll get:

- **Username**: `admin`
- **Password**: (randomly generated and saved to `admin_credentials.txt`)
- **Email**: `admin@laso-healthcare.com`
- **Admin URL**: `http://your-server-ip/admin`

## 🚀 How to Run Your System on VPS

### Development Mode (Quick Testing)
```bash
cd /path/to/your/laso-wise
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

### Production Mode (Recommended)
The complete setup script configures:
- **Gunicorn** as the WSGI server
- **Nginx** as reverse proxy
- **PostgreSQL** as database
- **Redis** for caching
- **Systemd services** for auto-start

Services will start automatically and restart on reboot.

## 🔧 Management Commands

### Check Service Status
```bash
sudo systemctl status laso-gunicorn
sudo systemctl status nginx
sudo systemctl status postgresql
```

### View Logs
```bash
sudo journalctl -u laso-gunicorn -f
sudo tail -f /opt/laso/logs/gunicorn_error.log
```

### Restart Services
```bash
sudo systemctl restart laso-gunicorn
sudo systemctl restart nginx
```

### Update Application
```bash
cd /opt/laso/laso-wise
git pull origin master
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart laso-gunicorn
```

## 🛠️ Troubleshooting Common Issues

### 1. Admin Login Not Working
```bash
# Reset admin password
cd /opt/laso/laso-wise
sudo -u laso venv/bin/python manage.py changepassword admin
```

### 2. Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
sudo -u laso venv/bin/python manage.py check --database default
```

### 3. Static Files Not Loading
```bash
# Recollect static files
cd /opt/laso/laso-wise
sudo -u laso venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart nginx
```

### 4. Permission Issues
```bash
# Fix ownership
sudo chown -R laso:laso /opt/laso/

# Fix permissions
sudo chmod -R 755 /opt/laso/laso-wise/
```

## 📁 Important File Locations

- **Application**: `/opt/laso/laso-wise/`
- **Virtual Environment**: `/opt/laso/laso-wise/venv/`
- **Configuration**: `/opt/laso/laso-wise/.env`
- **Admin Credentials**: `/opt/laso/admin_credentials.txt`
- **Logs**: `/opt/laso/logs/`
- **Static Files**: `/opt/laso/laso-wise/staticfiles/`
- **Media Files**: `/opt/laso/laso-wise/media/`

## 🔒 Security Recommendations

1. **Change admin password** after first login
2. **Configure email settings** in `.env` file
3. **Set up SSL/HTTPS** using Let's Encrypt
4. **Configure firewall** rules (UFW)
5. **Set up regular backups**
6. **Monitor logs** for suspicious activity
7. **Keep system updated**

## 📞 Next Steps

1. **Run the appropriate script** based on your setup
2. **Access your admin panel** using the generated credentials
3. **Change the admin password** immediately
4. **Configure email settings** for production
5. **Set up SSL certificate** for HTTPS
6. **Configure regular backups**

## 🎉 Success Indicators

You'll know everything is working when:
- ✅ All migrations run without errors
- ✅ Admin user is created successfully
- ✅ You can access the admin panel
- ✅ Static files load correctly
- ✅ All services are running

---

**Need Help?** Check the logs first:
```bash
sudo journalctl -u laso-gunicorn -f
sudo tail -f /opt/laso/logs/gunicorn_error.log
```

Your LASO Healthcare System is ready to deploy! 🚀