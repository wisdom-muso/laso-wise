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
        libxslt-dev

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy the project
COPY . .

# Use .env if it exists, otherwise use .env.example
RUN if [ ! -f .env ]; then cp .env.example .env; fi

# Create necessary directories
RUN mkdir -p /usr/src/app/staticfiles /usr/src/app/media

# Set proper permissions
RUN chmod +x manage.py

# Expose the port
EXPOSE 8005

# Command to run the server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8005"]