FROM python:3.11-alpine

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apk update \
    && apk add --no-cache \
        nano \
        gobject-introspection-dev \
        pango-dev \
        cairo-dev \
        libffi-dev \
        libmagic \
        libxml2-dev \
        libxslt-dev \
        wget

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy the project
COPY . .

# Create necessary directories
RUN mkdir -p /usr/src/app/staticfiles /usr/src/app/media

# Create necessary scripts if they don't exist
RUN if [ ! -f "collect_static.sh" ]; then \
        echo "collect_static.sh not found, creating it..."; \
        echo '#!/bin/sh' > collect_static.sh; \
        echo 'python manage.py collectstatic --noinput' >> collect_static.sh; \
    fi && \
    if [ ! -f "setup_app.sh" ]; then \
        echo "setup_app.sh not found, creating it..."; \
        echo '#!/bin/sh' > setup_app.sh; \
        echo 'mkdir -p core/views staticfiles media logs' >> setup_app.sh; \
        echo 'touch core/views/__init__.py' >> setup_app.sh; \
    fi && \
    chmod +x collect_static.sh setup_app.sh

# Create core/views directory and __init__.py file
RUN mkdir -p core/views && \
    if [ ! -f "core/views/__init__.py" ]; then \
        echo "# This file makes the views directory a Python package" > core/views/__init__.py; \
    fi

# Run static files collection
RUN echo "Running static files collection script..." && \
    python manage.py collectstatic --noinput

# Set proper permissions
RUN chmod +x manage.py

# Expose the port
EXPOSE 8005

# Command to run the server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8005"]