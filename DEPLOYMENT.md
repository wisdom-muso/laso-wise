# LASO Digital Health - Professional Deployment Guide

This guide provides comprehensive instructions for deploying LASO Digital Health on your VPS using Docker with professional best practices.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Environment Configuration](#environment-configuration)
4. [SSL Certificate Setup](#ssl-certificate-setup)
5. [Production Deployment](#production-deployment)
6. [Monitoring and Health Checks](#monitoring-and-health-checks)
7. [Backup and Recovery](#backup-and-recovery)
8. [Maintenance](#maintenance)
9. [Troubleshooting](#troubleshooting)
10. [Security Considerations](#security-considerations)

## Prerequisites

### System Requirements

- **Operating System**: Ubuntu 20.04+ or CentOS 8+ (recommended)
- **RAM**: Minimum 2GB, recommended 4GB+
- **Storage**: Minimum 20GB free space
- **CPU**: 2+ cores recommended
- **Network**: Public IP address and domain name (for SSL)

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+ (or docker-compose 1.29+)
- Git (for updates)
- curl (for health checks)

### Domain and DNS

- A domain name pointing to your VPS IP address
- DNS A record: `your-domain.com` → `your-vps-ip`
- DNS A record: `www.your-domain.com` → `your-vps-ip`

## Quick Start

### 1. Install Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo systemctl enable docker
sudo systemctl start docker

# Log out and back in to apply group changes
```

### 2. Clone and Setup

```bash
# Clone the repository
git clone <your-repository-url> laso-digital-health
cd laso-digital-health

# Make scripts executable
chmod +x run.sh
chmod +x deployment/scripts/*.sh
```

### 3. Configure Environment

```bash
# Copy environment template
cp env.template .env.prod

# Edit production environment
nano .env.prod
```

### 4. Deploy

```bash
# Start production deployment
./run.sh prod
```

## Environment Configuration

### Required Variables

Edit `.env.prod` and set the following required variables:

```bash
# Core Django Settings
DEBUG=False
SECRET_KEY=your-very-secure-secret-key-here-change-this-in-production

# Domain Settings
DOMAIN=your-domain.com
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# SSL Configuration
SSL_ENABLED=true
HTTP_PORT=80
HTTPS_PORT=443

# Security Settings
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True
```

### Optional Database Configuration

For production, consider using PostgreSQL:

```bash
# Uncomment database service in docker-compose.prod.yml
# Then configure:
DATABASE_URL=postgresql://laso_user:secure_password@db:5432/laso_db
POSTGRES_DB=laso_db
POSTGRES_USER=laso_user
POSTGRES_PASSWORD=secure_database_password
```

### Email Configuration

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## SSL Certificate Setup

### Automatic SSL with Let's Encrypt

The deployment script can automatically obtain SSL certificates:

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot

# Deploy with automatic SSL setup
./run.sh prod
```

### Manual SSL Certificate

If you have your own SSL certificates:

```bash
# Copy certificates to deployment/nginx/ssl/
cp your-cert.pem deployment/nginx/ssl/cert.pem
cp your-private-key.pem deployment/nginx/ssl/key.pem

# Generate DH parameters (optional but recommended)
openssl dhparam -out deployment/nginx/ssl/dhparam.pem 2048
```

## Production Deployment

### Standard Deployment

```bash
# Full production deployment
./run.sh prod

# Check status
./run.sh status

# View logs
./run.sh logs
```

### Advanced Deployment Options

```bash
# Deploy with monitoring
docker-compose -f docker-compose.prod.yml --profile monitoring up -d

# Deploy with automatic updates
docker-compose -f docker-compose.prod.yml --profile watchtower up -d

# Deploy specific services
docker-compose -f docker-compose.prod.yml up -d web nginx
```

### Deployment Commands

| Command | Description |
|---------|-------------|
| `./run.sh prod` | Start production deployment |
| `./run.sh stop` | Stop all containers |
| `./run.sh restart` | Restart application |
| `./run.sh update` | Update and restart |
| `./run.sh logs [service]` | View logs |
| `./run.sh status` | Show service status |
| `./run.sh health` | Check application health |
| `./run.sh shell [service]` | Open shell in container |
| `./run.sh clean` | Clean up Docker resources |

## Monitoring and Health Checks

### Health Check Endpoints

The application provides several health check endpoints:

- `https://your-domain.com/health/` - Simple health check
- `https://your-domain.com/health/detailed/` - Detailed health information
- `https://your-domain.com/health/ready/` - Readiness check
- `https://your-domain.com/health/live/` - Liveness check
- `https://your-domain.com/metrics/` - Prometheus metrics

### Monitoring Stack (Optional)

Enable monitoring with Prometheus and Grafana:

```bash
# Deploy with monitoring
docker-compose -f docker-compose.prod.yml --profile monitoring up -d

# Access Grafana
open http://your-domain.com:3000
# Default login: admin/admin (change immediately)

# Access Prometheus
open http://your-domain.com:9090
```

### Log Management

```bash
# View application logs
./run.sh logs web

# View nginx logs
./run.sh logs nginx

# Follow logs in real-time
./run.sh logs -f

# View Docker logs directly
docker-compose -f docker-compose.prod.yml logs --tail=100 -f
```

## Backup and Recovery

### Automatic Backups

Configure automatic backups in `.env.prod`:

```bash
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30
BACKUP_S3_BUCKET=your-backup-bucket
BACKUP_S3_ACCESS_KEY=your-s3-access-key
BACKUP_S3_SECRET_KEY=your-s3-secret-key
```

### Manual Backup

```bash
# Create backup
./deployment/scripts/backup.sh

# List backups
./deployment/scripts/restore.sh --list

# Create backup without compression
./deployment/scripts/backup.sh --no-compress
```

### Restore from Backup

```bash
# List available backups
./deployment/scripts/restore.sh --list

# Restore latest backup
./deployment/scripts/restore.sh 1

# Restore specific backup file
./deployment/scripts/restore.sh /path/to/backup.tar.gz

# Restore only database
./deployment/scripts/restore.sh --database-only 1
```

### Scheduled Backups

Set up automated backups with cron:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /path/to/laso-digital-health/deployment/scripts/backup.sh
```

## Maintenance

### Regular Updates

```bash
# Update application
./run.sh update

# Update Docker images
docker-compose -f docker-compose.prod.yml pull
./run.sh restart
```

### Database Maintenance

```bash
# Access database shell (SQLite)
./run.sh shell web
python manage.py dbshell

# Access PostgreSQL shell
./run.sh shell db
psql -U laso_user -d laso_db

# Run Django migrations
./run.sh shell web
python manage.py migrate
```

### SSL Certificate Renewal

```bash
# Renew Let's Encrypt certificates
sudo certbot renew --dry-run  # Test renewal
sudo certbot renew           # Actual renewal

# Restart nginx to load new certificates
docker-compose -f docker-compose.prod.yml restart nginx
```

### Performance Optimization

```bash
# Clean up Docker system
./run.sh clean

# Optimize database (PostgreSQL)
./run.sh shell db
vacuumdb -U laso_user -d laso_db --analyze --verbose

# Clear Django cache
./run.sh shell web
python manage.py shell -c "from django.core.cache import cache; cache.clear()"
```

## Troubleshooting

### Common Issues

#### 1. Container Won't Start

```bash
# Check container logs
./run.sh logs web

# Check Docker daemon
sudo systemctl status docker

# Check disk space
df -h

# Check memory usage
free -h
```

#### 2. SSL Certificate Issues

```bash
# Check certificate validity
openssl x509 -in deployment/nginx/ssl/cert.pem -text -noout

# Test SSL configuration
nginx -t

# Check certificate expiration
./run.sh shell nginx
openssl x509 -in /etc/nginx/ssl/cert.pem -noout -dates
```

#### 3. Database Connection Issues

```bash
# Check database container
./run.sh status

# Check database logs
./run.sh logs db

# Test database connection
./run.sh shell web
python manage.py check --database
```

#### 4. Performance Issues

```bash
# Check resource usage
docker stats

# Check application metrics
curl https://your-domain.com/health/detailed/

# Check nginx access logs
./run.sh logs nginx | tail -100
```

### Debug Mode

Enable debug mode temporarily:

```bash
# Edit environment
nano .env.prod
# Set DEBUG=True temporarily

# Restart application
./run.sh restart

# Remember to disable debug mode in production!
```

### Log Analysis

```bash
# Search for errors
./run.sh logs | grep -i error

# Count requests by IP
./run.sh logs nginx | awk '{print $1}' | sort | uniq -c | sort -nr

# Monitor real-time errors
./run.sh logs -f | grep -i error
```

## Security Considerations

### Firewall Configuration

```bash
# Ubuntu UFW
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# CentOS firewalld
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### Security Headers

The nginx configuration includes security headers:
- HSTS (HTTP Strict Transport Security)
- Content Security Policy
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection

### Regular Security Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
sudo yum update -y                      # CentOS/RHEL

# Update Docker images
docker-compose -f docker-compose.prod.yml pull
./run.sh restart
```

### Access Control

- Change default passwords immediately
- Use strong, unique passwords
- Enable 2FA where possible
- Regularly audit user access
- Monitor access logs

### Data Protection

- Enable database encryption at rest
- Use encrypted connections (SSL/TLS)
- Regular security backups
- Implement proper backup encryption
- Follow GDPR/HIPAA compliance if applicable

## Support and Resources

### Documentation Links

- [Django Deployment Guide](https://docs.djangoproject.com/en/stable/howto/deployment/)
- [Docker Best Practices](https://docs.docker.com/develop/best-practices/)
- [Nginx Security](https://nginx.org/en/docs/http/securing_http_traffic_ssl.html)

### Getting Help

1. Check application logs: `./run.sh logs`
2. Check health endpoints: `curl https://your-domain.com/health/detailed/`
3. Review this documentation
4. Contact support team

### Performance Monitoring

Monitor these key metrics:
- Response time (< 2 seconds)
- Memory usage (< 80% of available)
- Disk usage (< 80% of available)
- SSL certificate expiration
- Database performance
- Error rates

---

**Note**: This deployment uses production-ready configurations with security best practices. Always test changes in a staging environment before applying to production.
