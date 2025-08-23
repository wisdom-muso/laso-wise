# 🚀 Laso Healthcare VPS Deployment Guide

This guide will help you deploy Laso Healthcare on your VPS server at `http://65.108.91.110/`.

## 📋 Prerequisites

- Ubuntu/Debian VPS server
- Root or sudo access
- Domain pointing to your VPS (optional)
- At least 2GB RAM recommended

## 🛠️ Step 1: Server Setup

### Connect to your VPS
```bash
ssh root@65.108.91.110
```

### Update system packages
```bash
apt update && apt upgrade -y
```

### Install required packages
```bash
apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server git curl
```

### Create a new user for the application
```bash
adduser laso
usermod -aG sudo laso
su - laso
```

## 🗄️ Step 2: Database Setup

### Configure PostgreSQL
```bash
sudo -u postgres psql
```

In PostgreSQL shell:
```sql
CREATE DATABASE laso_healthcare;
CREATE USER laso_user WITH PASSWORD 'your_secure_password_here';
ALTER ROLE laso_user SET client_encoding TO 'utf8';
ALTER ROLE laso_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE laso_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE laso_healthcare TO laso_user;
\q
```

## 📁 Step 3: Application Deployment

### Clone the repository
```bash
cd /home/laso
git clone https://github.com/your-org/laso-healthcare.git
cd laso-healthcare
```

### Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### Install Python dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

### Create environment configuration
```bash
nano .env
```

Add the following content:
```bash
# Database Configuration
DATABASE_URL=postgresql://laso_user:your_secure_password_here@localhost/laso_healthcare

# Security
SECRET_KEY=your-very-long-random-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,65.108.91.110

# Email Configuration (optional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# AI Services (optional)
OPENAI_API_KEY=your_openai_key_here
HUGGINGFACE_API_KEY=your_hf_key_here
```

### Update Django settings for production
```bash
nano meditrack/settings.py
```

Add at the end:
```python
# Production settings
import os
from decouple import config

if not DEBUG:
    # Database
    import dj_database_url
    DATABASES['default'] = dj_database_url.parse(config('DATABASE_URL'))
    
    # Static files
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    
    # Security settings
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
```

### Run database migrations and setup
```bash
python manage.py manage_migrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py setup_laso_healthcare --all
```

## 🔧 Step 4: Configure Gunicorn

### Create Gunicorn service file
```bash
sudo nano /etc/systemd/system/laso-healthcare.service
```

Add the following content:
```ini
[Unit]
Description=Laso Healthcare gunicorn daemon
Requires=laso-healthcare.socket
After=network.target

[Service]
Type=notify
User=laso
Group=laso
RuntimeDirectory=gunicorn
WorkingDirectory=/home/laso/laso-healthcare
ExecStart=/home/laso/laso-healthcare/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/run/gunicorn/laso-healthcare.sock \
          meditrack.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### Create Gunicorn socket file
```bash
sudo nano /etc/systemd/system/laso-healthcare.socket
```

Add the following content:
```ini
[Unit]
Description=Laso Healthcare gunicorn socket

[Socket]
ListenStream=/run/gunicorn/laso-healthcare.sock
SocketUser=www-data
SocketMode=660

[Install]
WantedBy=sockets.target
```

### Create runtime directory
```bash
sudo mkdir -p /run/gunicorn
sudo chown laso:laso /run/gunicorn
```

## 🌐 Step 5: Configure Nginx

### Create Nginx configuration
```bash
sudo nano /etc/nginx/sites-available/laso-healthcare
```

Add the following content:
```nginx
server {
    listen 80;
    server_name 65.108.91.110;

    client_max_body_size 100M;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /home/laso/laso-healthcare/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /home/laso/laso-healthcare/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn/laso-healthcare.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Enable the site
```bash
sudo ln -s /etc/nginx/sites-available/laso-healthcare /etc/nginx/sites-enabled/
sudo nginx -t
```

### Remove default Nginx site (optional)
```bash
sudo rm /etc/nginx/sites-enabled/default
```

## 🚀 Step 6: Start Services

### Start and enable services
```bash
# Start Gunicorn
sudo systemctl daemon-reload
sudo systemctl start laso-healthcare.socket
sudo systemctl enable laso-healthcare.socket
sudo systemctl start laso-healthcare.service
sudo systemctl enable laso-healthcare.service

# Start Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Check service status
```bash
sudo systemctl status laso-healthcare.service
sudo systemctl status nginx
sudo systemctl status redis-server
sudo systemctl status postgresql
```

## 🔒 Step 7: Security & Firewall

### Configure UFW firewall
```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### Set proper permissions
```bash
sudo chown -R laso:laso /home/laso/laso-healthcare
sudo chmod -R 755 /home/laso/laso-healthcare
```

## 🌟 Step 8: Access Your Application

Your Laso Healthcare system should now be accessible at:
```
http://65.108.91.110/
```

### Default Login Credentials
- **Admin**: `admin` / `admin123`
- **Doctor**: `dr_sarah` / `doctor123`
- **Patient**: `patient_john` / `patient123`
- **Receptionist**: `receptionist` / `receptionist123`

## 📊 Step 9: Optional - SSL Certificate (Recommended)

### Install Certbot for Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx
```

### Get SSL certificate (if you have a domain)
```bash
sudo certbot --nginx -d yourdomain.com
```

## 🔧 Maintenance Commands

### View application logs
```bash
sudo journalctl -u laso-healthcare.service -f
```

### Restart application
```bash
sudo systemctl restart laso-healthcare.service
```

### Update application
```bash
cd /home/laso/laso-healthcare
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart laso-healthcare.service
```

### Backup database
```bash
pg_dump -U laso_user -h localhost laso_healthcare > backup_$(date +%Y%m%d_%H%M%S).sql
```

## 🐛 Troubleshooting

### Check if services are running
```bash
sudo systemctl status laso-healthcare.service
sudo systemctl status nginx
curl -I http://localhost
```

### View error logs
```bash
# Application logs
sudo journalctl -u laso-healthcare.service --since "1 hour ago"

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### Common issues and solutions

1. **Permission denied errors**:
   ```bash
   sudo chown -R laso:laso /home/laso/laso-healthcare
   sudo systemctl restart laso-healthcare.service
   ```

2. **Database connection errors**:
   - Check PostgreSQL is running: `sudo systemctl status postgresql`
   - Verify database credentials in `.env` file
   - Test connection: `psql -U laso_user -h localhost -d laso_healthcare`

3. **Static files not loading**:
   ```bash
   python manage.py collectstatic --noinput
   sudo systemctl restart nginx
   ```

4. **502 Bad Gateway**:
   - Check Gunicorn socket: `sudo systemctl status laso-healthcare.socket`
   - Restart services: `sudo systemctl restart laso-healthcare.service nginx`

## 📈 Performance Optimization

### For production use, consider:

1. **Increase Gunicorn workers**:
   ```bash
   # Edit /etc/systemd/system/laso-healthcare.service
   # Change --workers 3 to --workers $(nproc --all)
   ```

2. **Enable Gzip compression in Nginx**:
   Add to server block:
   ```nginx
   gzip on;
   gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
   ```

3. **Set up log rotation**:
   ```bash
   sudo nano /etc/logrotate.d/laso-healthcare
   ```

## 🎉 Congratulations!

Your Laso Healthcare system is now deployed and running on your VPS! 

Visit `http://65.108.91.110/` to start using your healthcare management system.

---

**Need help?** Check the troubleshooting section above or contact support at support@laso-healthcare.com