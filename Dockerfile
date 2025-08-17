# Multi-stage build for Django backend
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    libmagic1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=laso.settings

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    libxml2 \
    libxslt1.1 \
    libffi8 \
    libjpeg62-turbo \
    libpng16-16 \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN addgroup --system django && \
    adduser --system --group django

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy project files
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p staticfiles media logs && \
    chown -R django:django /app && \
    chmod +x manage.py

# Create core/views directory if it doesn't exist
RUN mkdir -p core/views && \
    touch core/views/__init__.py && \
    chown -R django:django core/views

# Switch to django user
USER django

# Collect static files
RUN python manage.py collectstatic --noinput --clear

# Expose port
EXPOSE 8005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8005/api/health/', timeout=5)" || exit 1

# Start the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8005"]