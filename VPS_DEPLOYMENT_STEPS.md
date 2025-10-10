# 🚀 LASO Healthcare System - VPS Deployment Steps

## Quick Deployment for VPS: 65.108.91.110

### Option 1: One-Command Deployment (Recommended)

SSH into your VPS and run:

```bash
# Connect to your VPS
ssh root@65.108.91.110

# Run the complete deployment script
curl -fsSL https://raw.githubusercontent.com/lasoappwise/laso-wise/master/vps-deploy-complete.sh | bash
```

### Option 2: Manual Deployment

If you prefer to do it step by step:

#### Step 1: Connect to VPS
```bash
ssh root@65.108.91.110
```

#### Step 2: Install Docker (if not installed)
```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Start Docker
systemctl start docker
systemctl enable docker
```

#### Step 3: Clone Repository
```bash
# Clone the project
git clone https://github.com/lasoappwise/laso-wise.git
cd laso-wise
```

#### Step 4: Quick Deploy
```bash
# Run the quick deployment script
chmod +x quick-vps-deploy.sh
./quick-vps-deploy.sh
```

#### Step 5: Configure Firewall
```bash
# Allow necessary ports
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

## 🎯 After Deployment

Your application will be available at:
- **Website**: http://65.108.91.110/
- **Admin Panel**: http://65.108.91.110/admin/

**Admin Login:**
- Username: `admin`
- Password: `8gJW48Tz8YXDrF57`

## 🛠️ Management Commands

```bash
# Check status
cd laso-wise
docker compose ps

# View logs
docker compose logs -f

# Restart services
docker compose restart

# Stop services
docker compose down

# Update application
git pull origin master
docker compose down
docker compose up -d --build
```

## 🔧 Troubleshooting

### If deployment fails:
1. Check Docker is running: `systemctl status docker`
2. Check available space: `df -h`
3. Check memory: `free -h`
4. View logs: `docker compose logs`

### If port 80 is busy:
```bash
# Check what's using port 80
netstat -tulpn | grep :80

# Stop Apache if running
systemctl stop apache2
systemctl disable apache2
```

### If containers won't start:
```bash
# Restart Docker
systemctl restart docker

# Clean up and retry
docker system prune -f
docker compose down
docker compose up -d --build
```

## 📞 Support

If you need help:
1. Check the logs: `docker compose logs`
2. Verify all containers are running: `docker compose ps`
3. Test connectivity: `curl http://localhost`
4. Check firewall: `ufw status`

## 🔒 Security Notes

- Change the default admin password after first login
- Consider setting up SSL/HTTPS for production use
- Regularly update the system: `apt update && apt upgrade`
- Monitor logs for any suspicious activity