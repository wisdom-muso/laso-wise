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

# Remove duplicate static files to prevent conflicts
RUN echo "Removing duplicate static files..." && \
    if [ -d "static/ckeditor/ckeditor" ]; then echo "- Removing static/ckeditor/ckeditor" && rm -rf static/ckeditor/ckeditor; fi && \
    if [ -d "static/ckeditor/file-icons" ]; then echo "- Removing static/ckeditor/file-icons" && rm -rf static/ckeditor/file-icons; fi && \
    if [ -d "static/ckeditor/galleriffic" ]; then echo "- Removing static/ckeditor/galleriffic" && rm -rf static/ckeditor/galleriffic; fi && \
    if [ -f "static/ckeditor/ckeditor-init.js" ]; then echo "- Removing static/ckeditor/ckeditor-init.js" && rm -f static/ckeditor/ckeditor-init.js; fi && \
    if [ -f "static/ckeditor/ckeditor.css" ]; then echo "- Removing static/ckeditor/ckeditor.css" && rm -f static/ckeditor/ckeditor.css; fi && \
    if [ -f "static/ckeditor/fixups.js" ]; then echo "- Removing static/ckeditor/fixups.js" && rm -f static/ckeditor/fixups.js; fi && \
    if [ -d "static/unfold" ]; then echo "- Removing static/unfold" && rm -rf static/unfold; fi && \
    if [ -d "static/admin" ]; then echo "- Removing static/admin" && rm -rf static/admin; fi

# Set proper permissions
RUN chmod +x manage.py

# Expose the port
EXPOSE 8005

# Command to run the server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8005"]