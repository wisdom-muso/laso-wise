# 🐳 Docker Deployment Guide for Laso Healthcare

This guide will help you deploy the Laso Healthcare Django application using Docker containers.

## 📋 Prerequisites

- Docker Engine (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)
- At least 4GB RAM available for containers
- Git

## 🚀 Quick Start (Development)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd laso-healthcare

# Set environment variables
export SECRET_KEY="your-super-secret-key-here"
```

### 2. Start Development Environment

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up --build

# Or run in background
docker-compose -f docker-compose.dev.yml up -d --build
```

### 3. Initialize Database

```bash
# Run migrations
docker-compose -f docker-compose.dev.yml exec web python manage.py migrate

# Create superuser
docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser

# Load sample data (optional)
docker-compose -f docker-compose.dev.yml exec web python manage.py setup_laso_healthcare
```

### 4. Access the Application

- **Main Application**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **Health Check**: http://localhost:8000/health/

## 🏭 Production Deployment

### 1. Environment Setup

Create a `.env` file in the project root:

```bash
# Security
SECRET_KEY=your-very-long-random-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database
DATABASE_URL=postgresql://laso_user:laso_password@db:5432/laso_healthcare

# Redis
REDIS_URL=redis://redis:6379/0

# Email (optional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 2. SSL Certificate Setup

For production, you need SSL certificates. Place them in `nginx/ssl/`:

```bash
# Create SSL directory
mkdir -p nginx/ssl

# Copy your SSL certificates
cp your-certificate.crt nginx/ssl/cert.pem
cp your-private-key.key nginx/ssl/key.pem
```

### 3. Deploy Production Stack

```bash
# Build and start production services
docker-compose up -d --build

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

### 4. Monitor Services

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f web
docker-compose logs -f nginx
docker-compose logs -f db

# Check health
curl https://your-domain.com/health/
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Required |
| `DEBUG` | Debug mode | False |
| `DATABASE_URL` | Database connection string | PostgreSQL |
| `REDIS_URL` | Redis connection string | Redis |
| `ALLOWED_HOSTS` | Allowed hostnames | localhost |

### Port Configuration

| Service | Internal Port | External Port |
|---------|---------------|---------------|
| Django | 8000 | 8000 (dev) / 80,443 (prod) |
| PostgreSQL | 5432 | 5432 (dev) / - (prod) |
| Redis | 6379 | 6379 (dev) / - (prod) |

## 📊 Monitoring and Logs

### View Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs web
docker-compose logs nginx
docker-compose logs db

# Follow logs in real-time
docker-compose logs -f web
```

### Health Checks

The application includes health checks for:

- Database connectivity
- Redis connectivity
- Static files availability
- Overall application status

Access health check at: `http://localhost:8000/health/`

### Performance Monitoring

```bash
# Check resource usage
docker stats

# Check container health
docker-compose ps
```

## 🔄 Maintenance

### Database Backups

```bash
# Create backup
docker-compose exec db pg_dump -U laso_user laso_healthcare > backup.sql

# Restore backup
docker-compose exec -T db psql -U laso_user laso_healthcare < backup.sql
```

### Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Run migrations
docker-compose exec web python manage.py migrate
```

### Scaling

```bash
# Scale web workers
docker-compose up -d --scale web=3

# Scale celery workers
docker-compose up -d --scale celery=2
```

## 🛠️ Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   sudo netstat -tulpn | grep :8000
   
   # Kill the process or change port in docker-compose.yml
   ```

2. **Database Connection Issues**
   ```bash
   # Check database logs
   docker-compose logs db
   
   # Test connection
   docker-compose exec web python manage.py dbshell
   ```

3. **Static Files Not Loading**
   ```bash
   # Recollect static files
   docker-compose exec web python manage.py collectstatic --noinput
   ```

4. **Permission Issues**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   ```

### Debug Mode

For debugging, use the development compose file:

```bash
docker-compose -f docker-compose.dev.yml up --build
```

## 🔒 Security Considerations

1. **Change Default Passwords**: Update database and Redis passwords
2. **Use Strong Secret Key**: Generate a strong Django secret key
3. **SSL Certificates**: Use valid SSL certificates in production
4. **Firewall**: Configure firewall to only allow necessary ports
5. **Regular Updates**: Keep Docker images and dependencies updated

## 📈 Performance Optimization

1. **Enable Gzip**: Already configured in Nginx
2. **Static File Caching**: Configured with long cache times
3. **Database Optimization**: Use connection pooling
4. **Redis Caching**: Implement caching strategies
5. **CDN**: Consider using a CDN for static files

## 🆘 Support

For issues and questions:

1. Check the logs: `docker-compose logs`
2. Verify health check: `curl http://localhost:8000/health/`
3. Check service status: `docker-compose ps`
4. Review this documentation
5. Check Django documentation for specific errors

## 📝 Notes

- The development setup includes volume mounts for live code changes
- Production setup uses optimized images and configurations
- Health checks are configured for all services
- Logs are centralized and easily accessible
- Backup and restore procedures are documented
- Scaling options are available for high-traffic scenarios