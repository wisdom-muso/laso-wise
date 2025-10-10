# LASO Healthcare System - Complete VPS Deployment Guide

## 🚀 Quick Deployment for VPS: 65.108.91.110

This guide will help you deploy the LASO Healthcare System to your VPS with a single command.

## Prerequisites

- VPS with Ubuntu 20.04+ or similar Linux distribution
- Root or sudo access
- At least 2GB RAM and 20GB disk space
- Internet connection

## 🎯 One-Command Deployment

SSH into your VPS and run this single command:

```bash
curl -fsSL https://raw.githubusercontent.com/lasoappwise/laso-wise/master/vps-deploy-complete.sh | bash
```

Or if you prefer to download and inspect the script first:

```bash
wget https://raw.githubusercontent.com/lasoappwise/laso-wise/master/vps-deploy-complete.sh
chmod +x vps-deploy-complete.sh
./vps-deploy-complete.sh
```

## 📋 Manual Step-by-Step Deployment

If you prefer to deploy manually, follow these steps:

### Step 1: Connect to Your VPS

```bash
ssh root@65.108.91.110
# or
ssh your-username@65.108.91.110
```

### Step 2: Update System and Install Dependencies

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y curl wget git ufw

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add current user to docker group (if not root)
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker
```

### Step 3: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/lasoappwise/laso-wise.git
cd laso-wise
```

### Step 4: Configure Environment

```bash
# Copy the VPS environment configuration
cp .env.vps .env

# Edit the environment file if needed
nano .env
```

### Step 5: Deploy the Application

```bash
# Make deployment script executable
chmod +x deploy.sh

# Run the deployment
./deploy.sh
```

### Step 6: Configure Firewall

```bash
# Allow SSH (IMPORTANT - don't lock yourself out!)
sudo ufw allow ssh

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw --force enable

# Check firewall status
sudo ufw status
```

## 🔐 Access Information

After successful deployment:

- **Application URL**: http://65.108.91.110/
- **Admin Panel**: http://65.108.91.110/admin/
- **Admin Credentials**:
  - Username: `admin`
  - Password: `8gJW48Tz8YXDrF57`

## 🛠️ Management Commands

### Check Service Status
```bash
cd laso-wise
docker compose ps
```

### View Logs
```bash
cd laso-wise
docker compose logs -f
```

### Restart Services
```bash
cd laso-wise
docker compose restart
```

### Stop Services
```bash
cd laso-wise
docker compose down
```

### Update Application
```bash
cd laso-wise
git pull origin master
docker compose down
docker compose build --no-cache
docker compose up -d
```

## 🔧 Troubleshooting

### If containers fail to start:
```bash
# Check Docker status
sudo systemctl status docker

# Check logs
docker compose logs

# Restart Docker
sudo systemctl restart docker
```

### If database connection fails:
```bash
# Check if .env file exists and has correct values
cat .env

# Restart database container
docker compose restart db
```

### If port 80 is already in use:
```bash
# Check what's using port 80
sudo netstat -tulpn | grep :80

# Stop conflicting service (e.g., Apache)
sudo systemctl stop apache2
sudo systemctl disable apache2
```

## 🔒 Security Recommendations

1. **Change default admin password** after first login
2. **Set up SSL certificate** for HTTPS
3. **Configure regular backups**
4. **Update system packages regularly**
5. **Monitor application logs**

## 📊 System Requirements

- **Minimum**: 2GB RAM, 20GB disk, 1 CPU core
- **Recommended**: 4GB RAM, 50GB disk, 2 CPU cores
- **Operating System**: Ubuntu 20.04+, CentOS 8+, or similar

## 🆘 Support

If you encounter issues:

1. Check the logs: `docker compose logs`
2. Verify all containers are running: `docker compose ps`
3. Check system resources: `free -h` and `df -h`
4. Ensure firewall allows required ports
5. Verify DNS/IP configuration

## 📝 Notes

- The application will be available on port 80 (HTTP)
- Database data is persisted in Docker volumes
- Automatic backups are configured and stored in `./backups/`
- All logs are stored in Docker volumes and can be accessed via `docker compose logs`