# 🛠️ Troubleshooting Guide

## Common Deployment Issues

### 1. Cryptography Dependency Error

**Error**: `ERROR: No matching distribution found for cryptography==41.0.8`

**Solution**: This has been fixed in the updated requirements.txt. The cryptography version is now set to `>=42.0.0` for better compatibility with Python 3.11+.

### 2. PostgreSQL Connection Issues

**Error**: `django.db.utils.OperationalError: could not connect to server`

**Solutions**:
1. **Wait for PostgreSQL to start**: The database takes time to initialize
   ```bash
   docker-compose logs db
   ```

2. **Check PostgreSQL 17 health**:
   ```bash
   docker-compose exec db pg_isready -U laso_user -d laso_healthcare
   ```

3. **Reset database if corrupted**:
   ```bash
   docker-compose down -v
   docker-compose up --build -d
   ```

### 3. Build Context Issues

**Error**: Build fails with context errors

**Solution**: Make sure you're in the project root directory:
```bash
cd /path/to/laso-healthcare
docker-compose up --build
```

### 4. Permission Issues

**Error**: Permission denied errors in containers

**Solutions**:
1. **Fix file permissions**:
   ```bash
   sudo chown -R $USER:$USER .
   chmod +x deploy.sh
   ```

2. **SELinux issues** (CentOS/RHEL):
   ```bash
   sudo setsebool -P container_manage_cgroup true
   ```

### 5. Memory Issues

**Error**: Out of memory during build

**Solutions**:
1. **Increase Docker memory limit** (Docker Desktop):
   - Settings → Resources → Memory → Increase to 4GB+

2. **Free up system memory**:
   ```bash
   docker system prune -a
   ```

3. **Build with limited parallelism**:
   ```bash
   docker-compose build --parallel 1
   ```

### 6. Port Conflicts

**Error**: `Port 8000 is already in use`

**Solutions**:
1. **Find and kill process using port**:
   ```bash
   sudo lsof -ti:8000 | xargs sudo kill -9
   ```

2. **Change port in docker-compose.yml**:
   ```yaml
   ports:
     - "8001:8000"  # Use port 8001 instead
   ```

### 7. Static Files Not Loading

**Error**: CSS/JS files not loading (404 errors)

**Solutions**:
1. **Collect static files**:
   ```bash
   docker-compose exec web python manage.py collectstatic --noinput
   ```

2. **Check STATIC_URL in settings**:
   ```python
   STATIC_URL = '/static/'
   STATIC_ROOT = '/app/staticfiles'
   ```

### 8. Migration Issues

**Error**: Migration conflicts or database schema errors

**Solutions**:
1. **Reset migrations** (development only):
   ```bash
   docker-compose exec web python manage.py migrate --fake-initial
   ```

2. **Fresh database** (development only):
   ```bash
   docker-compose down -v
   docker volume prune
   docker-compose up --build -d
   ```

## Useful Commands

### Check Service Status
```bash
docker-compose ps
docker-compose logs -f
```

### Access Container Shell
```bash
docker-compose exec web bash
docker-compose exec db psql -U laso_user -d laso_healthcare
```

### View Real-time Logs
```bash
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f redis
```

### Database Operations
```bash
# Backup database
docker-compose exec db pg_dump -U laso_user laso_healthcare > backup.sql

# Restore database
docker-compose exec -T db psql -U laso_user laso_healthcare < backup.sql
```

### Performance Monitoring
```bash
# Check resource usage
docker stats

# Check disk usage
docker system df
```

## Environment-Specific Issues

### Development Environment
- Use `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up`
- Enable DEBUG mode in .env
- Use console email backend

### Production Environment
- Ensure DEBUG=False
- Set proper ALLOWED_HOSTS
- Configure email settings
- Use proper SECRET_KEY
- Set up SSL/TLS

## Getting Help

1. **Check logs first**: `docker-compose logs -f`
2. **Verify environment**: Check .env file settings
3. **Test connectivity**: Use health check endpoints
4. **Resource monitoring**: Check system resources

If issues persist, please provide:
- Error messages from logs
- System information (OS, Docker version)
- Environment configuration (without sensitive data)
- Steps to reproduce the issue