# 🚀 Deploy LASO Healthcare System to VPS: 65.108.91.110

## 🎯 Quick Start (Recommended)

The fastest way to deploy to your VPS:

### 1. Connect to your VPS
```bash
ssh root@65.108.91.110
```

### 2. Run the one-command deployment
```bash
curl -fsSL https://raw.githubusercontent.com/lasoappwise/laso-wise/master/vps-deploy-complete.sh | bash
```

That's it! The script will:
- ✅ Install Docker and Docker Compose
- ✅ Configure firewall settings
- ✅ Clone the repository
- ✅ Set up the environment
- ✅ Deploy all services
- ✅ Run database migrations
- ✅ Create admin user
- ✅ Verify deployment

## 🌐 Access Your Application

After deployment completes:

- **Website**: http://65.108.91.110/
- **Admin Panel**: http://65.108.91.110/admin/

**Admin Credentials:**
- Username: `admin`
- Password: `8gJW48Tz8YXDrF57`

## 🛠️ Alternative: Manual Deployment

If you prefer to deploy manually:

### Step 1: Prepare VPS
```bash
# Connect to VPS
ssh root@65.108.91.110

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl start docker
systemctl enable docker
```

### Step 2: Deploy Application
```bash
# Clone repository
git clone https://github.com/lasoappwise/laso-wise.git
cd laso-wise

# Run quick deployment
chmod +x quick-vps-deploy.sh
./quick-vps-deploy.sh
```

### Step 3: Configure Security
```bash
# Set up firewall
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

## 📊 What Gets Deployed

Your VPS will run these services:

1. **PostgreSQL Database** - Patient data storage
2. **Redis Cache** - Session management and caching
3. **Django Web Application** - Main healthcare system
4. **Celery Worker** - Background task processing
5. **Celery Beat** - Scheduled tasks
6. **Nginx** - Web server and reverse proxy
7. **Automated Backups** - Daily database backups

## 🔧 Management Commands

After deployment, you can manage your system:

```bash
# Check service status
cd /opt/laso-wise  # or wherever you deployed
docker compose ps

# View logs
docker compose logs -f

# Restart all services
docker compose restart

# Stop all services
docker compose down

# Update application
git pull origin master
docker compose down
docker compose up -d --build
```

## 🔍 Troubleshooting

### Common Issues and Solutions:

**Port 80 already in use:**
```bash
# Check what's using port 80
netstat -tulpn | grep :80

# Stop Apache if running
systemctl stop apache2
systemctl disable apache2
```

**Docker not starting:**
```bash
# Restart Docker service
systemctl restart docker

# Check Docker status
systemctl status docker
```

**Database connection issues:**
```bash
# Check if .env file exists
cat .env

# Restart database container
docker compose restart db
```

**Out of memory/disk space:**
```bash
# Check memory
free -h

# Check disk space
df -h

# Clean up Docker
docker system prune -f
```

## 🔒 Security Recommendations

1. **Change default password** immediately after first login
2. **Set up SSL certificate** for HTTPS (recommended for production)
3. **Regular updates**: `apt update && apt upgrade`
4. **Monitor logs**: `docker compose logs`
5. **Backup regularly**: Backups are automated but verify they're working

## 📞 Support

If you encounter issues:

1. **Check logs**: `docker compose logs`
2. **Verify services**: `docker compose ps`
3. **Test connectivity**: `curl http://localhost`
4. **Check firewall**: `ufw status`
5. **System resources**: `free -h` and `df -h`

## 🎉 Success!

Once deployed successfully, you'll have a fully functional healthcare management system with:

- 👥 Patient management
- 📅 Appointment scheduling
- 💊 Treatment tracking
- 🩺 Telemedicine capabilities
- 📊 Analytics and reporting
- 🔐 Secure admin interface

**Your LASO Healthcare System is ready to use!** 🏥✨