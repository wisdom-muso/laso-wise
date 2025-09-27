# 🏥 LASO Healthcare Management System - VPS Deployment Guide

## 📋 Overview

This guide will help you deploy the LASO Healthcare Management System on your VPS at `http://65.108.91.110/` using Docker containers with PostgreSQL database, Redis cache, and Nginx reverse proxy.

## 🔧 Prerequisites

### System Requirements
- **VPS**: Ubuntu 20.04+ or CentOS 8+ (recommended)
- **RAM**: Minimum 2GB, Recommended 4GB+
- **Storage**: Minimum 20GB free space
- **Network**: Open ports 80 (HTTP) and 443 (HTTPS)

### Required Software
- Docker Engine 20.10+
- Docker Compose 2.0+
- Git
- Curl

## 🚀 Quick Deployment (Automated)

### Step 1: Clone the Repository
```bash
# Clone the repository
git clone https://gitlab.com/wisdomlasome-group/laso-wise.git
cd laso-wise

# Switch to master branch
git checkout master
```

### Step 2: Run the Deployment Script
```bash
# Make the script executable
chmod +x deploy.sh

# Run the deployment
sudo ./deploy.sh
```

The script will automatically:
- ✅ Check system requirements
- ✅ Set up environment configuration
- ✅ Build and deploy Docker containers
- ✅ Run database migrations
- ✅ Create admin user
- ✅ Configure firewall
- ✅ Verify deployment

## 📖 Manual Deployment (Step by Step)

### Step 1: Install Docker and Docker Compose

#### For Ubuntu/Debian:
```bash
# Update package index
sudo apt update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again to apply group changes
```

#### For CentOS/RHEL:
```bash
# Install Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Step 2: Clone and Configure

```bash
# Clone the repository
git clone https://gitlab.com/wisdomlasome-group/laso-wise.git
cd laso-wise

# Copy production environment file
cp .env.production .env

# Review and modify environment variables if needed
nano .env
```

### Step 3: Deploy the Application

```bash
# Build and start all services
docker-compose -f docker-compose.production.yml up -d --build

# Wait for services to start (about 30 seconds)
sleep 30

# Check service status
docker-compose -f docker-compose.production.yml ps
```

### Step 4: Initialize the Database

```bash
# Run database migrations
docker-compose -f docker-compose.production.yml exec web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.production.yml exec web python manage.py collectstatic --noinput

# Create superuser
docker-compose -f docker-compose.production.yml exec web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@laso.com', '8gJW48Tz8YXDrF57')
    print('Superuser created!')
else:
    print('Admin user already exists')
"
```

### Step 5: Configure Firewall

```bash
# Install and configure UFW firewall
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

## 🌐 Access Your Application

Once deployment is complete, your LASO Healthcare System will be available at:

**🔗 Main URL:** http://65.108.91.110/

**🔐 Admin Panel:** http://65.108.91.110/admin/
- **Username:** `admin`
- **Password:** `8gJW48Tz8YXDrF57`

## 🏥 Available Features

### Core Healthcare Modules
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

## 🐳 Docker Services

The deployment includes the following services:

| Service | Container | Port | Description |
|---------|-----------|------|-------------|
| **PostgreSQL** | `laso_postgres` | 5432 | Primary database |
| **Redis** | `laso_redis` | 6379 | Cache and session store |
| **Django Web** | `laso_web` | 8000 | Main application |
| **Celery Worker** | `laso_celery` | - | Background tasks |
| **Celery Beat** | `laso_celery_beat` | - | Scheduled tasks |
| **Nginx** | `laso_nginx` | 80/443 | Reverse proxy |

## 🛠️ Management Commands

### View Logs
```bash
# View all logs
docker-compose -f docker-compose.production.yml logs

# Follow logs in real-time
docker-compose -f docker-compose.production.yml logs -f

# View specific service logs
docker-compose -f docker-compose.production.yml logs web
```

### Service Management
```bash
# Check service status
docker-compose -f docker-compose.production.yml ps

# Restart services
docker-compose -f docker-compose.production.yml restart

# Stop all services
docker-compose -f docker-compose.production.yml down

# Update and restart
docker-compose -f docker-compose.production.yml pull
docker-compose -f docker-compose.production.yml up -d
```

### Database Management
```bash
# Access PostgreSQL shell
docker-compose -f docker-compose.production.yml exec db psql -U laso_user -d laso_healthcare

# Create database backup
docker-compose -f docker-compose.production.yml exec db pg_dump -U laso_user laso_healthcare > backup.sql

# Restore database backup
docker-compose -f docker-compose.production.yml exec -T db psql -U laso_user -d laso_healthcare < backup.sql
```

### Django Management
```bash
# Access Django shell
docker-compose -f docker-compose.production.yml exec web python manage.py shell

# Create additional superuser
docker-compose -f docker-compose.production.yml exec web python manage.py createsuperuser

# Run custom management commands
docker-compose -f docker-compose.production.yml exec web python manage.py <command>
```

## 🔧 Configuration Files

### Environment Variables (.env)
```bash
# Django Settings
DEBUG=False
SECRET_KEY=hk$6b!2g*3q1o+0r@u4z#b@t@*j8=5f5+g3e#9ly2n^+%h5!z5
ALLOWED_HOSTS=65.108.91.110,localhost,127.0.0.1

# Database
USE_SQLITE=False
POSTGRES_DB=laso_healthcare
POSTGRES_USER=laso_user
POSTGRES_PASSWORD=laso2403

# Redis
REDIS_PASSWORD=laso2403

# Email (configure for production)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Docker Compose (docker-compose.production.yml)
- PostgreSQL 17 with persistent data
- Redis 7 with authentication
- Django web application with health checks
- Celery workers for background tasks
- Nginx reverse proxy with SSL support

### Nginx Configuration (docker/nginx/nginx.conf)
- Reverse proxy to Django application
- Static file serving
- Security headers
- Rate limiting
- WebSocket support

## 🔒 Security Considerations

### Production Security Checklist
- ✅ **Firewall**: Only ports 22, 80, 443 open
- ✅ **Database**: PostgreSQL only accessible from containers
- ✅ **Redis**: Password protected and internal only
- ✅ **Django**: DEBUG=False, secure secret key
- ✅ **Nginx**: Security headers enabled
- ⚠️ **SSL**: Configure SSL certificates for HTTPS
- ⚠️ **Backups**: Set up automated database backups

### SSL Certificate Setup (Optional)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d 65.108.91.110

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 Monitoring and Maintenance

### Health Checks
```bash
# Check application health
curl http://65.108.91.110/health/

# Check service status
docker-compose -f docker-compose.production.yml ps
```

### Log Monitoring
```bash
# Monitor error logs
docker-compose -f docker-compose.production.yml logs web | grep ERROR

# Monitor access logs
docker-compose -f docker-compose.production.yml logs nginx
```

### Performance Monitoring
```bash
# Check resource usage
docker stats

# Check disk usage
df -h
docker system df
```

## 🆘 Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check logs for errors
docker-compose -f docker-compose.production.yml logs

# Restart problematic service
docker-compose -f docker-compose.production.yml restart <service_name>
```

#### Database Connection Issues
```bash
# Check PostgreSQL logs
docker-compose -f docker-compose.production.yml logs db

# Verify database connectivity
docker-compose -f docker-compose.production.yml exec web python manage.py dbshell
```

#### Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER .
sudo chmod -R 755 .
```

#### Port Conflicts
```bash
# Check what's using port 80
sudo netstat -tulpn | grep :80

# Stop conflicting services
sudo systemctl stop apache2  # or nginx
```

## 📞 Support

For technical support or questions:
- **Repository**: https://gitlab.com/wisdomlasome-group/laso-wise
- **Issues**: Create an issue in the GitLab repository
- **Documentation**: Check the project README and wiki

## 🎉 Congratulations!

Your LASO Healthcare Management System is now successfully deployed and running on your VPS at `http://65.108.91.110/`. The system includes all healthcare management features with a robust, scalable architecture using Docker containers.

**Next Steps:**
1. Configure SSL certificates for HTTPS
2. Set up automated backups
3. Configure email settings for notifications
4. Customize the system for your healthcare organization
5. Train your staff on using the system

Enjoy your new healthcare management platform! 🏥✨