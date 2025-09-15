# LASO Healthcare System - VPS Deployment Guide

## Overview
This guide will help you deploy the LASO Healthcare System on your VPS with proper production configuration, security, and performance optimizations.

## Prerequisites
- Ubuntu 20.04+ or CentOS 8+ VPS
- Root or sudo access
- Domain name (recommended for SSL)
- At least 2GB RAM and 20GB storage

## 1. Server Setup

### Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### Install Required Packages
```bash
# Install Python, PostgreSQL, Nginx, and other dependencies
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx redis-server git curl

# Install Node.js (for frontend assets if needed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

## 2. Database Setup

### Configure PostgreSQL
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE laso_healthcare;
CREATE USER laso_user WITH PASSWORD 'your_secure_password_here';
ALTER ROLE laso_user SET client_encoding TO 'utf8';
ALTER ROLE laso_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE laso_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE laso_healthcare TO laso_user;
\q
```

### Configure Redis
```bash
# Start and enable Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test Redis connection
redis-cli ping
```

## 3. Application Deployment

### Create Application User
```bash
sudo adduser --system --group --home /opt/laso laso
sudo mkdir -p /opt/laso
sudo chown laso:laso /opt/laso
```

### Clone and Setup Application
```bash
# Switch to application user
sudo -u laso -i

# Clone the repository
cd /opt/laso
git clone <your-repository-url> laso-wise
cd laso-wise

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration
```bash
# Create environment file
sudo -u laso nano /opt/laso/laso-wise/.env
```

Add the following content to `.env`:
```env
# Django Settings
SECRET_KEY=your_very_secure_secret_key_here_minimum_50_characters
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-vps-ip

# Database Configuration
DATABASE_URL=postgresql://laso_user:your_secure_password_here@localhost:5432/laso_healthcare

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Email Configuration (Optional - for notifications)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Security Settings
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Media and Static Files
MEDIA_ROOT=/opt/laso/laso-wise/media
STATIC_ROOT=/opt/laso/laso-wise/staticfiles
```

### Database Migration
```bash
# Switch to application user and activate virtual environment
sudo -u laso -i
cd /opt/laso/laso-wise
source venv/bin/activate

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Create media directories
mkdir -p media/profile_pictures
mkdir -p media/medical_documents
```

## 4. Gunicorn Configuration

### Create Gunicorn Configuration
```bash
sudo -u laso nano /opt/laso/laso-wise/gunicorn.conf.py
```

Add the following content:
```python
# Gunicorn configuration file
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "/opt/laso/logs/gunicorn_access.log"
errorlog = "/opt/laso/logs/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = "laso_healthcare"

# Server mechanics
daemon = False
pidfile = "/opt/laso/laso-wise/gunicorn.pid"
user = "laso"
group = "laso"
tmp_upload_dir = None

# SSL (if using HTTPS directly with Gunicorn)
# keyfile = "/path/to/your/private.key"
# certfile = "/path/to/your/certificate.crt"
```

### Create Log Directory
```bash
sudo mkdir -p /opt/laso/logs
sudo chown laso:laso /opt/laso/logs
```

## 5. Systemd Service Configuration

### Create Gunicorn Service
```bash
sudo nano /etc/systemd/system/laso-gunicorn.service
```

Add the following content:
```ini
[Unit]
Description=Gunicorn instance to serve LASO Healthcare
After=network.target postgresql.service redis.service

[Service]
User=laso
Group=laso
WorkingDirectory=/opt/laso/laso-wise
Environment="PATH=/opt/laso/laso-wise/venv/bin"
ExecStart=/opt/laso/laso-wise/venv/bin/gunicorn --config gunicorn.conf.py laso.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Create Celery Service (for background tasks)
```bash
sudo nano /etc/systemd/system/laso-celery.service
```

Add the following content:
```ini
[Unit]
Description=Celery Service for LASO Healthcare
After=network.target redis.service

[Service]
Type=forking
User=laso
Group=laso
EnvironmentFile=/opt/laso/laso-wise/.env
WorkingDirectory=/opt/laso/laso-wise
ExecStart=/opt/laso/laso-wise/venv/bin/celery multi start worker1 \
    -A laso --pidfile=/opt/laso/logs/celery_%n.pid \
    --logfile=/opt/laso/logs/celery_%n%I.log --loglevel=INFO
ExecStop=/opt/laso/laso-wise/venv/bin/celery multi stopwait worker1 \
    --pidfile=/opt/laso/logs/celery_%n.pid
ExecReload=/opt/laso/laso-wise/venv/bin/celery multi restart worker1 \
    -A laso --pidfile=/opt/laso/logs/celery_%n.pid \
    --logfile=/opt/laso/logs/celery_%n%I.log --loglevel=INFO
Restart=always

[Install]
WantedBy=multi-user.target
```

### Enable and Start Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable laso-gunicorn
sudo systemctl enable laso-celery
sudo systemctl start laso-gunicorn
sudo systemctl start laso-celery

# Check status
sudo systemctl status laso-gunicorn
sudo systemctl status laso-celery
```

## 6. Nginx Configuration

### Create Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/laso-healthcare
```

Add the following content:
```nginx
upstream laso_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration (you'll need to obtain SSL certificates)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Client upload limit
    client_max_body_size 100M;

    # Static files
    location /static/ {
        alias /opt/laso/laso-wise/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /opt/laso/laso-wise/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    # Main application
    location / {
        proxy_pass http://laso_app;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $http_host;
        proxy_redirect off;
        proxy_buffering off;
    }

    # WebSocket support for real-time features
    location /ws/ {
        proxy_pass http://laso_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Enable Nginx Configuration
```bash
sudo ln -s /etc/nginx/sites-available/laso-healthcare /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 7. SSL Certificate Setup (Let's Encrypt)

### Install Certbot
```bash
sudo apt install certbot python3-certbot-nginx
```

### Obtain SSL Certificate
```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### Auto-renewal Setup
```bash
sudo crontab -e
```

Add the following line:
```bash
0 12 * * * /usr/bin/certbot renew --quiet
```

## 8. Firewall Configuration

### Configure UFW
```bash
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

## 9. Monitoring and Logging

### Create Log Rotation
```bash
sudo nano /etc/logrotate.d/laso-healthcare
```

Add the following content:
```
/opt/laso/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 laso laso
    postrotate
        systemctl reload laso-gunicorn
        systemctl reload laso-celery
    endscript
}
```

## 10. Backup Strategy

### Create Backup Script
```bash
sudo nano /opt/laso/backup.sh
```

Add the following content:
```bash
#!/bin/bash

# Configuration
BACKUP_DIR="/opt/laso/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="laso_healthcare"
DB_USER="laso_user"

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -U $DB_USER -h localhost $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# Media files backup
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz -C /opt/laso/laso-wise media/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

### Make Script Executable and Schedule
```bash
sudo chmod +x /opt/laso/backup.sh
sudo chown laso:laso /opt/laso/backup.sh

# Add to crontab for daily backups at 2 AM
sudo -u laso crontab -e
```

Add the following line:
```bash
0 2 * * * /opt/laso/backup.sh
```

## 11. Performance Optimization

### Configure PostgreSQL
```bash
sudo nano /etc/postgresql/12/main/postgresql.conf
```

Optimize these settings based on your VPS resources:
```
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

### Restart PostgreSQL
```bash
sudo systemctl restart postgresql
```

## 12. Health Checks and Monitoring

### Create Health Check Script
```bash
sudo nano /opt/laso/health_check.sh
```

Add the following content:
```bash
#!/bin/bash

# Check if services are running
services=("laso-gunicorn" "laso-celery" "postgresql" "redis-server" "nginx")

for service in "${services[@]}"; do
    if systemctl is-active --quiet $service; then
        echo "$service: OK"
    else
        echo "$service: FAILED"
        systemctl restart $service
    fi
done

# Check database connectivity
sudo -u laso /opt/laso/laso-wise/venv/bin/python /opt/laso/laso-wise/manage.py check --database default

# Check disk space
df -h /opt/laso
```

## 13. Running the System

### Start All Services
```bash
sudo systemctl start postgresql
sudo systemctl start redis-server
sudo systemctl start laso-gunicorn
sudo systemctl start laso-celery
sudo systemctl start nginx
```

### Check Service Status
```bash
sudo systemctl status laso-gunicorn
sudo systemctl status laso-celery
sudo systemctl status nginx
```

### View Logs
```bash
# Application logs
sudo tail -f /opt/laso/logs/gunicorn_error.log
sudo tail -f /opt/laso/logs/gunicorn_access.log

# System logs
sudo journalctl -u laso-gunicorn -f
sudo journalctl -u laso-celery -f
```

## 14. Accessing the System

Once deployed, you can access your system at:
- **Main Application**: https://your-domain.com
- **Admin Panel**: https://your-domain.com/admin/

### Default Login Credentials
- **Admin**: Use the superuser account you created during setup
- **Test Patient**: username: `patient1`, password: `patient123` (create via admin panel)

## 15. Maintenance Commands

### Update Application
```bash
sudo -u laso -i
cd /opt/laso/laso-wise
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart laso-gunicorn
sudo systemctl restart laso-celery
```

### Database Operations
```bash
# Create database backup
sudo -u laso pg_dump -U laso_user -h localhost laso_healthcare > backup.sql

# Restore database
sudo -u laso psql -U laso_user -h localhost laso_healthcare < backup.sql
```

## 16. Security Considerations

1. **Regular Updates**: Keep your system and dependencies updated
2. **Strong Passwords**: Use strong passwords for all accounts
3. **Firewall**: Only open necessary ports
4. **SSL/TLS**: Always use HTTPS in production
5. **Backup**: Regular automated backups
6. **Monitoring**: Set up monitoring and alerting
7. **Access Control**: Limit SSH access and use key-based authentication

## 17. Troubleshooting

### Common Issues

1. **Service won't start**: Check logs with `journalctl -u service-name`
2. **Database connection issues**: Verify PostgreSQL is running and credentials are correct
3. **Static files not loading**: Run `python manage.py collectstatic` and check Nginx configuration
4. **Permission issues**: Ensure proper ownership with `chown -R laso:laso /opt/laso/`

### Log Locations
- Application logs: `/opt/laso/logs/`
- Nginx logs: `/var/log/nginx/`
- PostgreSQL logs: `/var/log/postgresql/`
- System logs: `journalctl -u service-name`

## Support

For additional support or issues, check the application logs and system status. The health check endpoints are available at:
- `/health/` - Basic health check
- `/readiness/` - Readiness check
- `/liveness/` - Liveness check

---

**Note**: Replace `your-domain.com` and `your-vps-ip` with your actual domain and IP address throughout this guide.