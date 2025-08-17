# Django + React Medical System

A containerized medical system with Django backend and React frontend, configured for production deployment on VPS.

## 🚀 Quick Start (Production VPS)

```bash
# 1. Clone to your VPS
git clone <your-repo> && cd <project>

# 2. Setup environment
cp env.template .env
nano .env  # Update SECRET_KEY, POSTGRES_PASSWORD, etc.

# 3. Deploy to production
./run.sh start prod

# 4. Setup database (first time only)
./run.sh migrate
./run.sh superuser
```

**Your app will be live at: http://65.108.91.110**

## 🌐 Production URLs

- **Main Application:** http://65.108.91.110
- **Django Admin:** http://65.108.91.110/admin  
- **API Endpoints:** http://65.108.91.110/api

## 📋 Commands

| Command | Description |
|---------|-------------|
| `./run.sh start prod` | Deploy to production |
| `./run.sh start dev` | Run development mode |
| `./run.sh stop` | Stop all services |
| `./run.sh logs [service]` | View logs |
| `./run.sh status` | Check service status |
| `./run.sh migrate` | Run database migrations |
| `./run.sh superuser` | Create Django admin user |
| `./run.sh shell [service]` | Access container shell |
| `./run.sh backup` | Backup production database |
| `./run.sh help` | Show all commands |

## 🏗️ Production Architecture

```
Internet → Nginx (Port 80) → Django (Port 8005) + React (Port 3000)
                            ↘ PostgreSQL Database
```

**Services:**
- **Nginx**: Reverse proxy, static files, load balancing
- **Django**: Backend API with PostgreSQL  
- **React**: Frontend UI (built and served via nginx)
- **PostgreSQL**: Production database

## ⚙️ Configuration

### Environment Setup

1. **Copy template:**
   ```bash
   cp env.template .env
   ```

2. **Update key settings:**
   ```bash
   SECRET_KEY=your-new-secret-key
   POSTGRES_PASSWORD=secure-password
   ALLOWED_HOSTS=65.108.91.110,your-domain.com
   ```

3. **For HTTPS (optional):**
   ```bash
   CSRF_COOKIE_SECURE=True
   SESSION_COOKIE_SECURE=True
   CSRF_TRUSTED_ORIGINS=https://65.108.91.110
   ```

### Development vs Production

| Mode | Command | Database | Debug | URL |
|------|---------|----------|-------|-----|
| **Development** | `./run.sh start dev` | SQLite | Yes | http://localhost:8005 |
| **Production** | `./run.sh start prod` | PostgreSQL | No | http://65.108.91.110 |

## 🔧 Management

### Database Operations
```bash
# Run migrations
./run.sh migrate

# Create superuser
./run.sh superuser

# Backup database
./run.sh backup

# Database shell
./run.sh shell db
```

### Service Management
```bash
# View all service status
./run.sh status

# View nginx logs
./run.sh logs nginx

# Restart production services
./run.sh restart prod

# Access Django shell
./run.sh shell django
```

### Maintenance
```bash
# Clean up Docker resources
./run.sh cleanup

# Update and restart
git pull && ./run.sh restart prod
```

## 🛠️ Development

For local development:

```bash
# Start development environment
./run.sh start dev

# Access services
# Django: http://localhost:8005
# React: http://localhost:3000
```

## 📊 Monitoring

- **Health Check**: http://65.108.91.110/health/
- **Service Status**: `./run.sh status`
- **Logs**: `./run.sh logs [service]`

## 🔒 Security Features

- Nginx reverse proxy with security headers
- CSRF protection
- Rate limiting on API endpoints
- PostgreSQL with secure credentials
- Docker container isolation

## 📦 Requirements

- **VPS**: 2GB+ RAM, 20GB+ storage
- **Docker**: Latest version with `docker compose`
- **Ports**: 80 (HTTP) open to internet

## 🚨 Troubleshooting

### Common Issues

1. **Port 80 busy:**
   ```bash
   sudo lsof -i :80
   sudo systemctl stop apache2  # if running
   ```

2. **Database connection issues:**
   ```bash
   ./run.sh logs db
   ./run.sh shell db  # Check database
   ```

3. **Nginx config issues:**
   ```bash
   ./run.sh logs nginx
   ```

### Reset Everything
```bash
./run.sh cleanup
rm .env
cp env.template .env
# Edit .env with new values
./run.sh start prod
```

---

**Production Ready:** ✅ Configured for http://65.108.91.110 deployment