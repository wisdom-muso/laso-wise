# LASO Digital Health - Docker Setup Guide

## Overview

This project is configured to run with Docker Compose, providing both development and production environments. The setup includes:

- **Backend**: Django application running on port 8005
- **Frontend**: React application running on port 3000
- **Database**: SQLite (development) / PostgreSQL (production)
- **Reverse Proxy**: Nginx (production only)

## Quick Start

### Prerequisites

1. **Docker**: Install Docker and Docker Compose
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install docker.io docker-compose
   
   # macOS
   brew install docker docker-compose
   
   # Windows
   # Download Docker Desktop from https://www.docker.com/products/docker-desktop
   ```

2. **Git**: Clone the repository
   ```bash
   git clone <repository-url>
   cd laso-digital-health
   ```

### Development Environment

1. **Start the application**:
   ```bash
   ./run.sh dev
   ```

2. **Access the application**:
   - **Backend API**: http://localhost:8005
   - **Frontend**: http://localhost:3000
   - **Admin Panel**: http://localhost:8005/admin

3. **View logs**:
   ```bash
   ./run.sh logs
   ```

4. **Stop the application**:
   ```bash
   ./run.sh stop
   ```

### Production Environment

1. **Configure environment**:
   ```bash
   cp env.template .env.prod
   # Edit .env.prod with your production settings
   ```

2. **Start the application**:
   ```bash
   ./run.sh prod
   ```

3. **Access the application**:
   - **HTTP**: http://your-domain.com
   - **HTTPS**: https://your-domain.com (if SSL enabled)
   - **Frontend**: http://your-domain.com:3000
   - **Backend API**: http://your-domain.com:8005

## Configuration Files

### Docker Compose Files

- **`docker-compose.yml`**: Development configuration
- **`docker-compose.prod.yml`**: Production configuration

### Environment Files

- **`.env.dev`**: Development environment variables
- **`.env.prod`**: Production environment variables (create from `env.template`)

### Frontend Configuration

- **`frontend/vite.config.ts`**: Vite development server configuration
- **`frontend/nginx.conf`**: Nginx configuration for production frontend
- **`frontend/Dockerfile`**: Development Dockerfile
- **`frontend/Dockerfile.prod`**: Production Dockerfile

## Service Architecture

### Development Mode

```
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │
│   (Port 3000)   │◄──►│   (Port 8005)   │
│   React + Vite  │    │   Django        │
└─────────────────┘    └─────────────────┘
```

### Production Mode

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │    Database     │
│   (Port 3000)   │◄──►│   (Port 8005)   │◄──►│   (Optional)    │
│   React + Nginx │    │   Django + Gunicorn │   PostgreSQL    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         └───────────────────────┼───────────────────────┐
                                 │                       │
                    ┌─────────────────┐    ┌─────────────────┐
                    │   Nginx Proxy   │    │   SSL/TLS       │
                    │   (Port 80/443) │    │   (Let's Encrypt)│
                    └─────────────────┘    └─────────────────┘
```

## Port Configuration

| Service | Development | Production | Description |
|---------|-------------|------------|-------------|
| Backend | 8005 | 8005 | Django API server |
| Frontend | 3000 | 3000 | React application |
| Nginx | - | 80/443 | Reverse proxy (production) |
| Database | - | 5432 | PostgreSQL (optional) |

## API Proxy Configuration

The frontend is configured to proxy API requests to the backend:

- **Development**: Vite dev server proxies requests to `http://web:8005`
- **Production**: Nginx proxies requests to `http://web:8005`

### Proxied Endpoints

- `/api/*` → Backend API
- `/admin/*` → Django admin
- `/static/*` → Static files
- `/media/*` → Media files

## Environment Variables

### Development (.env.dev)

```bash
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8005,http://localhost:3000
CSRF_COOKIE_SECURE=False
SESSION_COOKIE_SECURE=False
FRONTEND_API_BASE=http://localhost:8005
```

### Production (.env.prod)

```bash
DEBUG=False
SECRET_KEY=your-very-secure-secret-key
DOMAIN=your-domain.com
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True
SSL_ENABLED=true
FRONTEND_API_BASE=https://your-domain.com
```

## Useful Commands

### Run Script Commands

```bash
./run.sh dev          # Start development environment
./run.sh prod         # Start production environment
./run.sh stop         # Stop all containers
./run.sh logs         # View logs
./run.sh status       # Show container status
./run.sh update       # Update application
./run.sh clean        # Clean up Docker resources
```

### Docker Compose Commands

```bash
# Development
docker-compose up -d                    # Start development containers
docker-compose down                     # Stop development containers
docker-compose logs -f                  # View development logs

# Production
docker-compose -f docker-compose.prod.yml up -d    # Start production containers
docker-compose -f docker-compose.prod.yml down     # Stop production containers
docker-compose -f docker-compose.prod.yml logs -f  # View production logs
```

### Container Management

```bash
# View running containers
docker ps

# Access container shell
docker exec -it <container-name> /bin/bash

# View container logs
docker logs <container-name>

# Rebuild containers
docker-compose build --no-cache
```

## Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   # Check what's using the port
   sudo lsof -i :8005
   sudo lsof -i :3000
   
   # Stop conflicting services
   sudo systemctl stop <service-name>
   ```

2. **Permission denied**:
   ```bash
   # Add user to docker group
   sudo usermod -aG docker $USER
   # Log out and back in
   ```

3. **Frontend not connecting to backend**:
   - Check if backend is running: `docker ps`
   - Check backend logs: `docker logs <backend-container>`
   - Verify proxy configuration in `frontend/vite.config.ts`

4. **Build failures**:
   ```bash
   # Clean and rebuild
   docker-compose down
   docker system prune -f
   docker-compose build --no-cache
   docker-compose up -d
   ```

### Validation

Run the validation script to check your configuration:

```bash
./validate_config.sh
```

This will verify:
- Docker Compose files are properly configured
- Frontend and backend configurations are correct
- Environment files are set up properly
- All required files are present

## Development Workflow

1. **Start development environment**:
   ```bash
   ./run.sh dev
   ```

2. **Make changes to code**:
   - Backend changes are automatically reloaded
   - Frontend changes are automatically reloaded

3. **View logs**:
   ```bash
   ./run.sh logs
   ```

4. **Stop when done**:
   ```bash
   ./run.sh stop
   ```

## Production Deployment

1. **Set up your domain**:
   - Configure DNS to point to your server
   - Ensure ports 80, 443, 3000, and 8005 are open

2. **Configure environment**:
   ```bash
   cp env.template .env.prod
   # Edit .env.prod with your production settings
   ```

3. **Deploy**:
   ```bash
   ./run.sh prod
   ```

4. **Monitor**:
   ```bash
   ./run.sh status
   ./run.sh logs
   ```

## Security Considerations

- **Development**: Uses HTTP and relaxed security settings
- **Production**: Uses HTTPS and strict security settings
- **Secrets**: Store sensitive data in environment variables
- **Updates**: Regularly update dependencies and base images
- **Backups**: Configure database backups for production

## Support

For issues and questions:
1. Check the troubleshooting section
2. Run the validation script
3. Check container logs
4. Review the configuration files