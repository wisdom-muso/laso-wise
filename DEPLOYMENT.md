# LASO Healthcare VPS Deployment Guide

## Quick VPS Deployment

### Prerequisites

- Ubuntu 20.04+ VPS
- Root or sudo access
- Domain name (optional)

### One-Command Deployment

1. Clone the repository:
```bash
git clone <repository-url>
cd laso-wise
```

2. Run the deployment script:
```bash
./deploy-vps.sh
```

3. Access the application:
- Main application: http://your-domain:3000
- Admin panel: http://your-domain:3000/admin/
- Default admin credentials: admin/admin123

## What the Deployment Script Does

The deployment script automatically:
- Installs Docker and Docker Compose
- Configures firewall settings (UFW)
- Sets up SSL certificates (self-signed)
- Creates secure environment configuration
- Deploys all services on port 3000
- Runs database migrations
- Creates admin user
- Starts all services

## Post-Deployment Steps

1. **Change Admin Password**: Login to admin panel and change the default password
2. **Configure Email**: Update email settings in `.env` for notifications
3. **SSL Certificates**: Replace self-signed certificates with proper SSL certificates
4. **Domain Setup**: Point your domain to the VPS IP address
5. **Backup Configuration**: Secure your `.env` file

## Admin Dashboard Integration

The admin panel features:
- **Unified Interface**: Django Unfold integration with custom dashboard
- **Landing Dashboard**: Admins land on comprehensive dashboard first
- **Full Admin Access**: Complete Django admin functionality available
- **Real-time Metrics**: Live system statistics and health monitoring
- **User Management**: Comprehensive user and role management

## Docker Services (Port 3000)

- **web**: Django application (internal port 8000, exposed as 3000)
- **db**: PostgreSQL database (port 5432)
- **redis**: Redis cache (port 6379)
- **nginx**: Reverse proxy (ports 80, 443)
- **celery**: Background task worker
- **celery-beat**: Scheduled task scheduler

## Useful Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Update application
git pull && docker-compose up -d --build

# Backup database
docker-compose exec db pg_dump -U laso_user laso_healthcare > backup.sql

# Access Django shell
docker-compose exec web python manage.py shell
```

## Security Features

- Firewall configuration (UFW)
- CSRF protection
- SQL injection prevention
- XSS protection
- Secure session management
- Rate limiting
- SSL/TLS support
- Auto-generated secure passwords

## Monitoring

- Health check endpoints: `/health/`, `/readiness/`, `/liveness/`
- Comprehensive logging
- Automated database backups (daily, 7-day retention)
- Performance monitoring

## Troubleshooting

### Common Issues

1. **Port 3000 not accessible**: Check firewall settings with `sudo ufw status`
2. **Database connection errors**: Verify PostgreSQL is running with `docker-compose ps`
3. **Redis authentication errors**: Check Redis password in `.env`
4. **Static files not loading**: Run `docker-compose exec web python manage.py collectstatic`

### Service Status

Check if all services are running:
```bash
docker-compose ps
```

View service logs:
```bash
docker-compose logs [service-name]
```

## Environment Configuration

The `.env` file contains all configuration. Key variables:

- `DEBUG=False`: Production mode
- `SECRET_KEY`: Auto-generated secure key
- `ALLOWED_HOSTS`: Your domain and localhost
- `POSTGRES_PASSWORD`: Auto-generated secure password
- `REDIS_PASSWORD`: Auto-generated secure password

## Support

For support and questions, please contact the development team or create an issue in the repository.