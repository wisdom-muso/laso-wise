# 🐳 Docker Setup for Laso Healthcare

This guide provides comprehensive instructions for running Laso Healthcare using Docker containers.

## 📋 Prerequisites

- **Docker** 20.10 or higher
- **Docker Compose** 2.0 or higher
- **Git** (to clone the repository)
- At least **4GB RAM** and **10GB disk space**

### Install Docker

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install docker.io docker-compose-plugin
sudo systemctl enable docker
sudo usermod -aG docker $USER
# Log out and back in for group changes to take effect
```

#### macOS
```bash
# Install Docker Desktop from https://www.docker.com/products/docker-desktop
# Or using Homebrew:
brew install --cask docker
```

#### Windows
Download and install Docker Desktop from https://www.docker.com/products/docker-desktop

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd laso-healthcare
```

### 2. Initial Setup
```bash
# Make scripts executable
chmod +x docker-start.sh docker-manage.sh

# Run the initial setup (this will guide you through configuration)
./docker-start.sh
```

The setup script will:
- Create a `.env` file from the template
- Generate a secure `SECRET_KEY`
- Build Docker images
- Set up the database
- Create an admin user
- Load sample data

### 3. Access the Application
After successful startup:
- **Main Application**: http://localhost
- **Admin Panel**: http://localhost/admin
- **Health Check**: http://localhost/health

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

## 🛠️ Docker Services

The Docker setup includes the following services:

| Service | Container | Port | Description |
|---------|-----------|------|-------------|
| **web** | laso_web | 8000 | Django application server |
| **db** | laso_postgres | 5432 | PostgreSQL database |
| **redis** | laso_redis | 6379 | Redis cache and session store |
| **celery** | laso_celery | - | Background task worker |
| **celery-beat** | laso_celery_beat | - | Scheduled task scheduler |
| **nginx** | laso_nginx | 80, 443 | Reverse proxy and static files |
| **db-backup** | laso_db_backup | - | Automated database backups |

## 📁 Directory Structure

```
laso-healthcare/
├── docker/                 # Docker configuration files
│   ├── nginx/              # Nginx configuration
│   ├── postgres/           # PostgreSQL initialization
│   └── backup/             # Backup scripts
├── logs/                   # Application logs
├── backups/                # Database backups
├── Dockerfile              # Main application Dockerfile
├── docker-compose.yml      # Production configuration
├── docker-compose.dev.yml  # Development overrides
├── docker-start.sh         # Initial setup script
├── docker-manage.sh        # Management script
└── .env.example            # Environment template
```

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Core Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,your-domain.com

# Database
POSTGRES_DB=laso_healthcare
POSTGRES_USER=laso_user
POSTGRES_PASSWORD=secure-password

# Redis
REDIS_PASSWORD=secure-redis-password

# Email (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# AI Services (Optional)
OPENAI_API_KEY=your-openai-key
HUGGINGFACE_API_KEY=your-hf-key
```

### Development vs Production

#### Development Mode
```bash
# Use development configuration with live reloading
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

#### Production Mode
```bash
# Use production configuration with Nginx
docker-compose up -d
```

## 🔧 Management Commands

Use the `docker-manage.sh` script for common operations:

```bash
# Service Management
./docker-manage.sh start        # Start all services
./docker-manage.sh stop         # Stop all services
./docker-manage.sh restart      # Restart all services
./docker-manage.sh status       # Show service status

# Application Management
./docker-manage.sh shell        # Django shell
./docker-manage.sh bash         # Container bash shell
./docker-manage.sh migrate      # Run migrations
./docker-manage.sh collectstatic # Collect static files

# Monitoring
./docker-manage.sh logs         # View logs
./docker-manage.sh logs-f       # Follow logs
./docker-manage.sh health       # Health check

# Database Operations
./docker-manage.sh backup       # Create database backup
./docker-manage.sh restore backup_file.sql  # Restore from backup

# Maintenance
./docker-manage.sh clean        # Clean up containers
./docker-manage.sh rebuild      # Rebuild images
./docker-manage.sh update       # Update and restart
```

## 🗄️ Database Management

### Backups
Automated daily backups are created and stored in the `./backups/` directory.

#### Manual Backup
```bash
./docker-manage.sh backup
```

#### Restore from Backup
```bash
./docker-manage.sh restore backup_20240115_120000.sql
```

### Direct Database Access
```bash
# Connect to PostgreSQL
docker-compose exec db psql -U laso_user -d laso_healthcare

# Or using pgAdmin (add to docker-compose.yml if needed)
```

## 📊 Monitoring and Health Checks

### Health Check Endpoints
- `/health/` - Comprehensive health check
- `/readiness/` - Kubernetes readiness probe
- `/liveness/` - Kubernetes liveness probe

### Monitoring Services
```bash
# Check service status
./docker-manage.sh status

# View real-time logs
./docker-manage.sh logs-f

# Monitor resource usage
docker stats

# Check container health
docker-compose ps
```

## 🔒 Security Considerations

### Production Security
1. **Environment Variables**: Never commit `.env` files
2. **SSL/TLS**: Configure SSL certificates in `docker/nginx/ssl/`
3. **Firewall**: Expose only necessary ports (80, 443)
4. **Database**: Use strong passwords and limit network access
5. **Updates**: Regularly update base images and dependencies

### SSL Configuration
To enable HTTPS:

1. Place SSL certificates in `docker/nginx/ssl/`
2. Uncomment SSL configuration in `docker/nginx/nginx.conf`
3. Update `.env` with `SECURE_SSL_REDIRECT=True`

## 🚀 Production Deployment

### Recommended Production Setup

1. **Server Requirements**
   - 4+ CPU cores
   - 8+ GB RAM
   - 50+ GB SSD storage
   - Ubuntu 20.04+ or similar

2. **Domain Configuration**
   ```bash
   # Update .env
   ALLOWED_HOSTS=your-domain.com,www.your-domain.com
   DEBUG=False
   ```

3. **SSL Setup**
   ```bash
   # Using Let's Encrypt
   sudo apt install certbot
   sudo certbot certonly --standalone -d your-domain.com
   
   # Copy certificates to docker/nginx/ssl/
   ```

4. **Start Production Services**
   ```bash
   docker-compose up -d
   ```

### Load Balancing
For high-availability setups, run multiple web containers:

```yaml
# In docker-compose.yml
services:
  web:
    deploy:
      replicas: 3
```

## 🐛 Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
docker-compose logs web

# Check resource usage
docker system df
docker system prune  # Clean up if needed
```

#### Database Connection Issues
```bash
# Check database status
docker-compose exec db pg_isready -U laso_user

# Reset database
docker-compose down -v
docker-compose up -d db
# Wait for startup, then:
./docker-manage.sh migrate
```

#### Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER .
chmod +x docker-start.sh docker-manage.sh
```

#### Port Conflicts
```bash
# Check what's using ports
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :5432

# Stop conflicting services or change ports in docker-compose.yml
```

### Debug Mode
Enable debug mode for troubleshooting:

```bash
# In .env
DEBUG=True

# Restart services
./docker-manage.sh restart
```

## 🔄 Updates and Maintenance

### Regular Updates
```bash
# Pull latest code
git pull

# Update and restart
./docker-manage.sh update
```

### Database Migrations
```bash
# After code updates
./docker-manage.sh migrate
```

### Image Updates
```bash
# Rebuild with latest base images
./docker-manage.sh rebuild
```

## 📝 Development

### Development Workflow
```bash
# Start development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Make changes to code (auto-reloads)
# Access at http://localhost:8000

# Run tests
docker-compose exec web python manage.py test

# Create migrations
./docker-manage.sh makemigrations
```

### Adding New Dependencies
1. Update `requirements.txt`
2. Rebuild the image: `./docker-manage.sh rebuild`

## 🆘 Support

For Docker-related issues:
1. Check this documentation
2. View logs: `./docker-manage.sh logs`
3. Check health: `./docker-manage.sh health`
4. Review Docker Compose configuration
5. Consult the main project documentation

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [PostgreSQL Docker Documentation](https://hub.docker.com/_/postgres)
- [Redis Docker Documentation](https://hub.docker.com/_/redis)

---

**Happy containerizing! 🐳**