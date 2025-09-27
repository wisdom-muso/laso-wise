# 🏥 LASO Healthcare - Complete VPS Deployment Guide

## 📋 Overview

This guide provides a complete, tested deployment process for the LASO Healthcare Management System on your VPS at `http://65.108.91.110/`. This deployment includes fixes for CSRF verification issues and login problems.

## 🔧 Prerequisites

### System Requirements
- **VPS**: Ubuntu 20.04+ or CentOS 8+
- **RAM**: Minimum 2GB, Recommended 4GB+
- **Storage**: Minimum 20GB free space
- **Network**: Open ports 80, 443, and 3000

### Required Software
- Docker Engine 20.10+
- Docker Compose 2.0+
- Git
- Curl

## 🚀 One-Command Deployment

### Quick Start (Recommended)

```bash
# Clone the repository
git clone https://gitlab.com/wisdomlasome-group/laso-wise.git
cd laso-wise

# Run the deployment script
chmod +x deploy-vps-final.sh
sudo ./deploy-vps-final.sh
```

This script will automatically:
- ✅ Install Docker and Docker Compose
- ✅ Configure firewall settings
- ✅ Set up environment variables
- ✅ Deploy all Docker services
- ✅ Run database migrations
- ✅ Create admin user
- ✅ Fix CSRF and login issues
- ✅ Verify deployment

## 📖 Manual Deployment (Step by Step)

### Step 1: System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y curl wget git openssl ufw

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again to apply group changes
```

### Step 2: Clone and Configure

```bash
# Clone the repository
git clone https://gitlab.com/wisdomlasome-group/laso-wise.git
cd laso-wise

# Use the VPS-specific environment file
cp .env.vps .env

# Review the configuration (optional)
nano .env
```

### Step 3: Configure Firewall

```bash
# Configure UFW firewall
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 3000
sudo ufw --force enable
```

### Step 4: Deploy Services

```bash
# Stop any conflicting services
sudo systemctl stop apache2 2>/dev/null || true
sudo systemctl disable apache2 2>/dev/null || true

# Deploy the application
docker-compose down --remove-orphans || true
docker-compose build --no-cache
docker-compose up -d

# Wait for services to start
sleep 30
```

### Step 5: Initialize Database

```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Create admin user
docker-compose exec web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@laso.com', 'admin123')
    print('Admin user created!')
else:
    print('Admin user already exists')
"
```

## 🌐 Access Your Application

### URLs
- **Main Application**: http://65.108.91.110:3000
- **Admin Panel**: http://65.108.91.110:3000/admin/

### Admin Credentials
- **Username**: `admin`
- **Password**: `admin123`

## 🔒 CSRF and Login Issues - FIXED

### What Was Fixed

1. **CSRF Configuration**: Updated `settings.py` to use environment variables for `CSRF_TRUSTED_ORIGINS`
2. **Environment Variables**: Added `CSRF_TRUSTED_ORIGINS` to docker-compose.yml
3. **VPS-Specific Config**: Created `.env.vps` with proper CSRF origins for your VPS
4. **Domain Configuration**: Configured for both HTTP and HTTPS on your VPS IP

### CSRF Trusted Origins Configured
```
http://65.108.91.110
https://65.108.91.110
http://65.108.91.110:3000
https://65.108.91.110:3000
http://65.108.91.110:80
https://65.108.91.110:443
```

## 🐳 Docker Services

| Service | Container | Port | Description |
|---------|-----------|------|-------------|
| **PostgreSQL** | `laso_postgres` | 5432 | Primary database |
| **Redis** | `laso_redis` | 6379 | Cache and session store |
| **Django Web** | `laso_web` | 3000 | Main application |
| **Celery Worker** | `laso_celery` | - | Background tasks |
| **Celery Beat** | `laso_celery_beat` | - | Scheduled tasks |
| **Nginx** | `laso_nginx` | 80/443 | Reverse proxy |

## 🛠️ Management Commands

### Service Management
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop all services
docker-compose down

# Update application
git pull && docker-compose up -d --build
```

### Database Management
```bash
# Access PostgreSQL shell
docker-compose exec db psql -U laso_user -d laso_healthcare

# Create backup
docker-compose exec db pg_dump -U laso_user laso_healthcare > backup.sql

# Restore backup
docker-compose exec -T db psql -U laso_user -d laso_healthcare < backup.sql
```

### Django Management
```bash
# Access Django shell
docker-compose exec web python manage.py shell

# Create additional superuser
docker-compose exec web python manage.py createsuperuser

# Check CSRF configuration
docker-compose exec web python -c "
import os
from django.conf import settings
print('CSRF_TRUSTED_ORIGINS:', settings.CSRF_TRUSTED_ORIGINS)
print('ALLOWED_HOSTS:', settings.ALLOWED_HOSTS)
"
```

## 🔧 Configuration Files

### Environment Variables (.env.vps)
```bash
DEBUG=False
SECRET_KEY=hk$6b!2g*3q1o+0r@u4z#b@t@*j8=5f5+g3e#9ly2n^+%h5!z5
ALLOWED_HOSTS=65.108.91.110,localhost,127.0.0.1,*
CSRF_TRUSTED_ORIGINS=http://65.108.91.110,https://65.108.91.110,http://65.108.91.110:3000,https://65.108.91.110:3000

# Database
POSTGRES_DB=laso_healthcare
POSTGRES_USER=laso_user
POSTGRES_PASSWORD=laso2403

# Redis
REDIS_PASSWORD=laso2403
```

## 🏥 Healthcare Features

### Core Modules
- **👥 Patient Management** - Complete patient records and profiles
- **📅 Appointment Scheduling** - Doctor availability and booking system
- **💻 Telemedicine** - Video consultation platform
- **📋 Treatment Management** - Medical history, prescriptions, lab tests
- **🔬 Medical Imaging** - X-ray and diagnostic image management
- **👨‍⚕️ User Management** - Doctors, patients, and staff accounts
- **📊 Analytics & Reporting** - Healthcare statistics and insights

### Technical Features
- **🔒 Security** - CSRF protection, secure authentication
- **⚡ Performance** - Redis caching, optimized database queries
- **📱 Responsive** - Mobile-friendly interface
- **🔄 Real-time** - WebSocket support for live updates
- **📧 Notifications** - Email and system notifications
- **🤖 AI Integration** - OpenAI and HuggingFace API support

## 🔒 Security Considerations

### Production Security Checklist
- ✅ **Firewall**: Configured with UFW
- ✅ **Database**: PostgreSQL secured with password
- ✅ **Redis**: Password protected
- ✅ **Django**: DEBUG=False, secure secret key
- ✅ **CSRF**: Properly configured for VPS domain
- ⚠️ **SSL**: Consider adding SSL certificates
- ⚠️ **Backups**: Set up automated database backups

### SSL Certificate Setup (Optional)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# If you have a domain name pointing to your VPS:
sudo certbot --nginx -d yourdomain.com

# For IP-based setup, use self-signed certificates:
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/laso.key \
    -out /etc/ssl/certs/laso.crt \
    -subj "/C=US/ST=State/L=City/O=LASO/CN=65.108.91.110"
```

## 🆘 Troubleshooting

### Common Issues and Solutions

#### 1. CSRF Verification Failed
**Solution**: The deployment script fixes this automatically. If you still encounter issues:
```bash
# Check CSRF configuration
docker-compose exec web python -c "
from django.conf import settings
print('CSRF_TRUSTED_ORIGINS:', settings.CSRF_TRUSTED_ORIGINS)
"

# Restart web service
docker-compose restart web
```

#### 2. Admin Login Not Working
**Solution**: 
```bash
# Reset admin password
docker-compose exec web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
admin = User.objects.get(username='admin')
admin.set_password('admin123')
admin.save()
print('Password reset successfully')
"
```

#### 3. Services Not Starting
```bash
# Check logs
docker-compose logs

# Check system resources
free -h
df -h

# Restart services
docker-compose down
docker-compose up -d
```

#### 4. Port Conflicts
```bash
# Check what's using port 3000
sudo netstat -tulpn | grep :3000

# Stop conflicting services
sudo pkill -f ":3000"
```

#### 5. Database Connection Issues
```bash
# Check PostgreSQL logs
docker-compose logs db

# Test database connection
docker-compose exec web python manage.py dbshell
```

## 📊 Monitoring and Maintenance

### Health Checks
```bash
# Check application health
curl http://65.108.91.110:3000/health/

# Check admin panel
curl http://65.108.91.110:3000/admin/

# Check service status
docker-compose ps
```

### Performance Monitoring
```bash
# Check resource usage
docker stats

# Check disk usage
df -h
docker system df

# Monitor logs
docker-compose logs -f --tail=100
```

### Backup Strategy
```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T db pg_dump -U laso_user laso_healthcare > "backup_${DATE}.sql"
find . -name "backup_*.sql" -mtime +7 -delete
EOF

chmod +x backup.sh

# Add to crontab for daily backups
echo "0 2 * * * /path/to/laso-wise/backup.sh" | crontab -
```

## 📞 Support

For technical support:
- **Repository**: https://gitlab.com/wisdomlasome-group/laso-wise
- **Issues**: Create an issue in the GitLab repository
- **Documentation**: Check project README and wiki

## 🎉 Deployment Complete!

Your LASO Healthcare Management System is now successfully deployed on your VPS at `http://65.108.91.110:3000` with all CSRF and login issues resolved.

### Next Steps:
1. 🔑 Change the default admin password
2. 📧 Configure email settings for notifications
3. 🔒 Set up SSL certificates if needed
4. 💾 Configure automated backups
5. 👥 Create user accounts for your healthcare staff
6. 🏥 Customize the system for your organization

**Your healthcare management platform is ready to use!** 🏥✨

---

*Generated by LASO Healthcare Deployment Script v2.0*