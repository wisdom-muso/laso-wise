# Django + React Integration Setup

This project has been configured with separate Docker containers for Django backend and React frontend, with seamless API integration.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Git (for cloning/updating)

### Run the Application

1. **Start all services:**
   ```bash
   ./run-dev.sh start
   ```

2. **Access the applications:**
   - **React Frontend:** http://localhost:3000
   - **Django Backend:** http://localhost:8005  
   - **Django Admin:** http://localhost:8005/admin
   - **API Endpoints:** http://localhost:8005/api

### First Time Setup

After starting the services, you'll need to run Django migrations and create a superuser:

```bash
# Run database migrations
./run-dev.sh migrate

# Create Django superuser
./run-dev.sh superuser
```

## 📋 Available Commands

The `run-dev.sh` script provides convenient commands for development:

| Command | Description |
|---------|-------------|
| `./run-dev.sh start` | Build and start all services |
| `./run-dev.sh stop` | Stop all services |
| `./run-dev.sh restart` | Restart all services |
| `./run-dev.sh status` | Show service status |
| `./run-dev.sh logs [service]` | View logs (optionally for specific service) |
| `./run-dev.sh migrate` | Run Django migrations |
| `./run-dev.sh superuser` | Create Django superuser |
| `./run-dev.sh collectstatic` | Collect Django static files |
| `./run-dev.sh shell [service]` | Open shell in container (django/frontend) |
| `./run-dev.sh manage "<command>"` | Run Django management command |
| `./run-dev.sh cleanup` | Clean up Docker resources |
| `./run-dev.sh help` | Show all commands |

### Examples:
```bash
# View Django logs
./run-dev.sh logs django

# View React logs  
./run-dev.sh logs frontend

# Run Django shell
./run-dev.sh shell django

# Run custom Django command
./run-dev.sh manage "makemigrations"
```

## 🏗️ Architecture

### Services
- **Django Backend** (Port 8005): Python/Django REST API
- **React Frontend** (Port 3000): Node.js/React with Nginx

### Key Files
- `Dockerfile.django` - Django backend container
- `frontend/Dockerfile.react` - React frontend container  
- `docker-compose.dev.yml` - Development orchestration
- `frontend/src/lib/api.ts` - API client configuration
- `core/api.py` - Django API endpoints
- `run-dev.sh` - Development helper script

## 🔧 API Integration Features

### Authentication
- JWT token-based authentication
- User registration and login endpoints
- Session management with Django

### CSRF Protection
- Automatic CSRF token handling
- Secure cross-origin requests
- Cookie-based session management

### Error Handling
- Automatic request retries on network errors
- Comprehensive error logging
- Graceful fallback handling

### Endpoints
- `GET /api/health/` - Health check
- `GET /api/csrf/` - Get CSRF token
- `POST /api/auth/login/` - User login
- `POST /api/auth/register/` - User registration
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/me/` - Current user info
- `GET /api/dashboard/stats/` - Dashboard statistics

## 🛠️ Development

### Backend Development (Django)
```bash
# Access Django shell
./run-dev.sh shell django

# Run migrations
./run-dev.sh migrate

# Create new app
./run-dev.sh manage "startapp myapp"

# Run tests
./run-dev.sh manage "test"
```

### Frontend Development (React)
```bash
# Access frontend container
./run-dev.sh shell frontend

# Install new package (restart required)
npm install package-name
```

### Database
- Uses SQLite by default for development
- Database file: `db.sqlite3` (auto-created)
- Persistent storage via Docker volumes

## 🔍 Troubleshooting

### Common Issues

1. **Port conflicts:**
   ```bash
   # Check what's using the ports
   lsof -i :8005
   lsof -i :3000
   ```

2. **Database issues:**
   ```bash
   # Reset database
   ./run-dev.sh stop
   rm db.sqlite3
   ./run-dev.sh start
   ./run-dev.sh migrate
   ```

3. **Docker issues:**
   ```bash
   # Clean up everything
   ./run-dev.sh cleanup
   ./run-dev.sh start
   ```

4. **Check service health:**
   ```bash
   # View service status
   ./run-dev.sh status
   
   # Check specific service logs
   ./run-dev.sh logs django
   ./run-dev.sh logs frontend
   ```

### Health Check URLs
- Django: http://localhost:8005/api/health/
- React: http://localhost:3000/health

## 📦 Production Deployment

For production deployment:

1. **Build production images:**
   ```bash
   docker build -f Dockerfile.django -t laso-django:prod .
   docker build -f frontend/Dockerfile.react -t laso-react:prod ./frontend
   ```

2. **Environment variables:**
   - Set `DEBUG=False` for Django
   - Configure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`
   - Use PostgreSQL instead of SQLite
   - Set secure session/CSRF cookie settings

3. **Use production compose file:**
   - Create `docker-compose.prod.yml` based on development version
   - Add proper volumes for persistent data
   - Configure reverse proxy (nginx) if needed

## 🧪 Testing

Run the setup validation:
```bash
python3 test-setup.py
```

This will check:
- All required files are present
- Django and React configurations
- API integration setup
- Docker configuration
- Service health

## 📝 Notes

- **Database:** SQLite is used for development. For production, switch to PostgreSQL
- **CORS:** Configured to allow requests between React (3000) and Django (8005)
- **Static Files:** Django serves static files via whitenoise
- **Media Files:** Handled by Django with volume persistence
- **Hot Reload:** React has hot reload enabled for development
- **Debug Mode:** Django runs in debug mode for development

## 🎯 Next Steps

1. **Add user authentication to React components**
2. **Implement protected routes in React**
3. **Add form validation and error handling**
4. **Configure production database (PostgreSQL)**
5. **Set up CI/CD pipeline**
6. **Add comprehensive testing**

## 📚 Documentation

- [Django REST Framework](https://www.django-rest-framework.org/)
- [React](https://reactjs.org/)
- [Vite](https://vitejs.dev/)
- [Docker](https://docs.docker.com/)
- [NextUI](https://nextui.org/)

---

**Status:** ✅ Ready for development with full Django + React integration