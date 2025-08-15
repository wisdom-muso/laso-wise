# Laso Digital Health Platform

A Django-based healthcare platform for managing doctors, patients, and appointments.

## Features

- Modern admin interface with Django Unfold
- Secure CSRF protection
- Docker-ready deployment
- Responsive design
- RESTful API
- CKEditor integration for rich text editing

## Quick Start

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/davidlasomvp-group/lasoai.git
   cd lasoai
   ```

2. Run the application:
   ```bash
   # Development mode (default)
   ./run.sh
   
   # Or explicitly specify development
   ./run.sh dev
   
   # Production mode
   ./run.sh production
   ```

3. Access the application:
   - Development: http://65.108.91.110:8005 (Django API) + http://65.108.91.110:3000 (React Frontend)
   - Production (default mapping): http://65.108.91.110:12000

### Manual Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/davidlasomvp-group/lasoai.git
   cd lasoai
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `env.template`:
   ```bash
   cp env.template .env
   ```

5. Apply migrations:
   ```bash
   python manage.py migrate
   ```

6. Run the development server:
   ```bash
   python manage.py runserver 0.0.0.0:8005
   ```

7. Access the application at http://localhost:8005

## Docker Commands

The `run.sh` script provides a unified interface for managing the application:

```bash
# Development mode (default)
./run.sh

# Production mode
./run.sh production

# Stop all containers
./run.sh stop

# Clean up (stop containers and remove volumes)
./run.sh clean

# Show help
./run.sh help
```

### Manual Docker Commands

If you prefer to use Docker commands directly:

```bash
# Development
docker-compose up --build

# Production
docker-compose -f docker-compose.prod.yml up --build -d

# Stop containers
docker-compose down
docker-compose -f docker-compose.prod.yml down
```

## Environment Variables

Copy `env.template` to `.env` and configure the following variables:

- `DEBUG`: Set to "False" in production
- `SECRET_KEY`: Django secret key
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `CSRF_TRUSTED_ORIGINS`: Comma-separated list of trusted origins for CSRF
- `CSRF_COOKIE_SECURE`: Set to "True" in production
- `SESSION_COOKIE_SECURE`: Set to "True" in production

## Admin Interface

The admin interface has been enhanced with Django Unfold for a modern, user-friendly experience. Access it at `/admin/` with your superuser credentials.

## Static Files Management

The application uses several packages that include static files which can cause duplicate file warnings during collectstatic:

1. **django-ckeditor**: For rich text editing
2. **django-unfold**: For admin UI enhancements
3. **Django Admin**: Default admin static files

The project includes a fix for handling all duplicate static files that may occur during the collectstatic process. This is automatically handled in the following ways:

1. The `collect_static.sh` script removes duplicate static files before running collectstatic
2. Both Dockerfiles include the same fix to ensure clean builds
3. If you encounter warnings about duplicate static files, run `./collect_static.sh` to resolve them

## Security Features

- CSRF protection configured for secure form submissions
- Secure cookie settings for production
- Environment-based configuration
- Proper error handling for CSRF failures

## Project Structure

```
lasoai/
├── docker-compose.yml          # Development Docker configuration (8005)
├── docker-compose.prod.yml     # Production Docker configuration (nginx 12000->80)
├── Dockerfile                  # Development Docker image (exposes 8005)
├── Dockerfile.prod            # Production Docker image (exposes 8005)
├── run.sh                     # Unified run script
├── env.template               # Environment variables template
├── requirements.txt           # Python dependencies
├── manage.py                  # Django management script
├── laso/                      # Main Django project
├── core/                      # Core app
├── accounts/                  # User accounts app
├── doctors/                   # Doctors management app
├── patients/                  # Patients management app
├── bookings/                  # Appointments app
├── mobile_clinic/             # Mobile clinic app
├── vitals/                    # Patient vitals app
├── dashboard/                 # Dashboard app
├── sync_monitor/              # Sync monitoring app
└── deployment/                # Production deployment files
```

## License

[License information]