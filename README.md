# Laso Digital Health Platform

A Django-based healthcare platform for managing doctors, patients, and appointments.

## Features

- Modern admin interface with Django Unfold
- Secure CSRF protection
- Docker-ready deployment
- Responsive design
- RESTful API
- CKEditor integration for rich text editing

## Development Setup

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/davidlasomvp-group/lasoai.git
   cd lasoai
   ```

2. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```

3. Build and run the Docker containers:
   ```bash
   docker-compose up --build
   ```

4. Access the application at http://localhost:8005

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

4. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
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

## Production Deployment

For production deployment, use the Docker Compose production configuration:

```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

This will:
1. Build the application with production settings
2. Run the application on port 8005
3. Set up Nginx as a reverse proxy

## Environment Variables

Key environment variables:

- `DEBUG`: Set to "False" in production
- `SECRET_KEY`: Django secret key
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `CSRF_TRUSTED_ORIGINS`: Comma-separated list of trusted origins for CSRF
- `DJANGO_PORT`: Port for the Django application (default: 8005)

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

## License

[License information]