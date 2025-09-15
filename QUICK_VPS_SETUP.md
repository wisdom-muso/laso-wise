# LASO Healthcare System - Quick VPS Setup Guide

This guide provides step-by-step instructions to deploy your LASO Healthcare System on a VPS and run the necessary database migrations.

## 🚀 Quick Start (Automated Setup)

### Option 1: Complete VPS Setup (Recommended for new servers)

```bash
# 1. Connect to your VPS
ssh root@your-vps-ip

# 2. Clone your repository
git clone https://github.com/davidgotlaso/laso-wise.git
cd laso-wise

# 3. Run the automated setup script
sudo ./vps-setup-guide.sh
```

This script will:
- ✅ Install all system dependencies (Python, PostgreSQL, Redis, Nginx)
- ✅ Configure PostgreSQL database
- ✅ Set up the Django application
- ✅ Run all database migrations
- ✅ Create an admin superuser
- ✅ Configure Gunicorn and Nginx
- ✅ Set up firewall rules

### Option 2: Migrations Only (If system is already set up)

```bash
# If you already have the system installed and just need to run migrations
cd /path/to/your/laso-wise
./run-migrations.sh
```

## 🔧 Manual Setup (Step by Step)

If you prefer to set up manually or need to troubleshoot:

### Step 1: Update System and Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv python3-dev \
    postgresql postgresql-contrib redis-server nginx git curl \
    build-essential libpq-dev supervisor
```

### Step 2: Configure PostgreSQL Database

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user (replace 'your_password' with a secure password)
CREATE DATABASE laso_healthcare;
CREATE USER laso_user WITH PASSWORD 'your_secure_password';
ALTER ROLE laso_user SET client_encoding TO 'utf8';
ALTER ROLE laso_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE laso_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE laso_healthcare TO laso_user;
\q
```

### Step 3: Set Up Application

```bash
# Create application user
sudo adduser --system --group --home /opt/laso laso
sudo mkdir -p /opt/laso/logs
sudo chown -R laso:laso /opt/laso

# Clone repository
sudo -u laso git clone https://github.com/davidgotlaso/laso-wise.git /opt/laso/laso-wise
cd /opt/laso/laso-wise

# Create virtual environment
sudo -u laso python3 -m venv venv
sudo -u laso venv/bin/pip install --upgrade pip
sudo -u laso venv/bin/pip install -r requirements.txt
```

### Step 4: Configure Environment

```bash
# Create .env file
sudo -u laso nano /opt/laso/laso-wise/.env
```

Add the following content (replace values as needed):

```env
# Django Settings
SECRET_KEY=your_very_secure_secret_key_here_minimum_50_characters
DEBUG=False
ALLOWED_HOSTS=your-domain.com,your-vps-ip,localhost,127.0.0.1

# Database Configuration
DATABASE_URL=postgresql://laso_user:your_secure_password@localhost:5432/laso_healthcare

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Security Settings
CSRF_TRUSTED_ORIGINS=https://your-domain.com,http://your-vps-ip
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

### Step 5: Run Database Migrations

```bash
cd /opt/laso/laso-wise
sudo -u laso venv/bin/python manage.py makemigrations
sudo -u laso venv/bin/python manage.py migrate
sudo -u laso venv/bin/python manage.py collectstatic --noinput

# Create media directories
sudo -u laso mkdir -p media/profile_pictures
sudo -u laso mkdir -p media/medical_documents
```

### Step 6: Create Admin User

```bash
# Create superuser
sudo -u laso venv/bin/python manage.py createsuperuser
```

### Step 7: Configure Gunicorn Service

```bash
# Create Gunicorn configuration
sudo -u laso nano /opt/laso/laso-wise/gunicorn.conf.py
```

Add the Gunicorn configuration (see the full file in the automated script).

```bash
# Create systemd service
sudo nano /etc/systemd/system/laso-gunicorn.service
```

Add the service configuration and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable laso-gunicorn
sudo systemctl start laso-gunicorn
```

### Step 8: Configure Nginx

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/laso-healthcare
```

Add the Nginx configuration, then:

```bash
sudo ln -s /etc/nginx/sites-available/laso-healthcare /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. Admin Login Not Working

```bash
# Reset admin password
cd /opt/laso/laso-wise
sudo -u laso venv/bin/python manage.py changepassword admin
```

#### 2. Database Connection Issues

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
sudo -u laso venv/bin/python manage.py check --database default
```

#### 3. Static Files Not Loading

```bash
# Recollect static files
cd /opt/laso/laso-wise
sudo -u laso venv/bin/python manage.py collectstatic --noinput

# Check Nginx configuration
sudo nginx -t
sudo systemctl restart nginx
```

#### 4. Service Not Starting

```bash
# Check service logs
sudo journalctl -u laso-gunicorn -f

# Check service status
sudo systemctl status laso-gunicorn
```

#### 5. Permission Issues

```bash
# Fix ownership
sudo chown -R laso:laso /opt/laso/

# Fix permissions
sudo chmod -R 755 /opt/laso/laso-wise/
sudo chmod -R 644 /opt/laso/laso-wise/media/
```

## 📋 Useful Commands

### Service Management

```bash
# Start services
sudo systemctl start laso-gunicorn
sudo systemctl start nginx

# Stop services
sudo systemctl stop laso-gunicorn
sudo systemctl stop nginx

# Restart services
sudo systemctl restart laso-gunicorn
sudo systemctl restart nginx

# Check status
sudo systemctl status laso-gunicorn
sudo systemctl status nginx
```

### Application Management

```bash
# View application logs
sudo journalctl -u laso-gunicorn -f

# Access Django shell
cd /opt/laso/laso-wise
sudo -u laso venv/bin/python manage.py shell

# Run migrations
sudo -u laso venv/bin/python manage.py migrate

# Create superuser
sudo -u laso venv/bin/python manage.py createsuperuser
```

### Database Management

```bash
# Access PostgreSQL
sudo -u postgres psql laso_healthcare

# Create database backup
sudo -u laso pg_dump -U laso_user -h localhost laso_healthcare > backup.sql

# Restore database
sudo -u laso psql -U laso_user -h localhost laso_healthcare < backup.sql
```

## 🔐 Security Checklist

- [ ] Change default admin password
- [ ] Configure firewall (UFW)
- [ ] Set up SSL/HTTPS (Let's Encrypt)
- [ ] Configure email settings
- [ ] Set up regular backups
- [ ] Update system packages regularly
- [ ] Monitor logs for suspicious activity

## 🌐 Accessing Your System

After successful deployment:

- **Main Application**: `http://your-vps-ip`
- **Admin Panel**: `http://your-vps-ip/admin`
- **Health Check**: `http://your-vps-ip/health/`

## 📞 Support

If you encounter issues:

1. Check the logs: `sudo journalctl -u laso-gunicorn -f`
2. Verify service status: `sudo systemctl status laso-gunicorn`
3. Test database connection: `sudo -u laso venv/bin/python manage.py check --database default`
4. Check Nginx configuration: `sudo nginx -t`

---

**Note**: Replace `your-vps-ip`, `your-domain.com`, and password placeholders with your actual values.