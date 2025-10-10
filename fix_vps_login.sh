#!/bin/bash

# =============================================================================
# Fix VPS Login Authentication Issues
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔧 Fixing LASO Healthcare Login Authentication${NC}"
echo -e "${BLUE}=============================================${NC}"

# Check if we're in the right directory
if [ ! -f "docker-compose.production.yml" ]; then
    echo -e "${RED}❌ docker-compose.production.yml not found. Please run from project root.${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Stopping containers...${NC}"
docker compose -f docker-compose.production.yml down

echo -e "${YELLOW}Step 2: Rebuilding containers with updated settings...${NC}"
docker compose -f docker-compose.production.yml build --no-cache web

echo -e "${YELLOW}Step 3: Starting containers...${NC}"
docker compose -f docker-compose.production.yml up -d

echo -e "${YELLOW}Step 4: Waiting for services to be ready...${NC}"
sleep 30

echo -e "${YELLOW}Step 5: Running database migrations...${NC}"
docker compose -f docker-compose.production.yml exec -T web python manage.py migrate --run-syncdb

echo -e "${YELLOW}Step 6: Collecting static files...${NC}"
docker compose -f docker-compose.production.yml exec -T web python manage.py collectstatic --noinput

echo -e "${YELLOW}Step 7: Running authentication fix...${NC}"
docker compose -f docker-compose.production.yml exec -T web python /app/fix_login_authentication.py

echo -e "${YELLOW}Step 8: Testing login functionality...${NC}"

# Test admin login
echo -e "${BLUE}Testing admin login...${NC}"
ADMIN_TEST=$(docker compose -f docker-compose.production.yml exec -T web python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laso.settings')
django.setup()
from django.contrib.auth import authenticate
user = authenticate(username='admin', password='8gJW48Tz8YXDrF57')
print('SUCCESS' if user else 'FAILED')
")

if [[ "$ADMIN_TEST" == *"SUCCESS"* ]]; then
    echo -e "${GREEN}✅ Admin authentication test passed${NC}"
else
    echo -e "${RED}❌ Admin authentication test failed${NC}"
fi

# Test patient login
echo -e "${BLUE}Testing patient login...${NC}"
PATIENT_TEST=$(docker compose -f docker-compose.production.yml exec -T web python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laso.settings')
django.setup()
from django.contrib.auth import authenticate
user = authenticate(username='patient', password='testpatient123')
print('SUCCESS' if user else 'FAILED')
")

if [[ "$PATIENT_TEST" == *"SUCCESS"* ]]; then
    echo -e "${GREEN}✅ Patient authentication test passed${NC}"
else
    echo -e "${RED}❌ Patient authentication test failed${NC}"
fi

echo -e "${YELLOW}Step 9: Checking service status...${NC}"
docker compose -f docker-compose.production.yml ps

echo -e "${BLUE}=============================================${NC}"
echo -e "${GREEN}🎉 Login fix process completed!${NC}"
echo ""
echo -e "${YELLOW}📝 LOGIN CREDENTIALS:${NC}"
echo ""
echo -e "${BLUE}Admin Login:${NC}"
echo "  URL: http://65.108.91.110/admin/"
echo "  Username: admin"
echo "  Password: 8gJW48Tz8YXDrF57"
echo ""
echo -e "${BLUE}Patient Login:${NC}"
echo "  URL: http://65.108.91.110/login/"
echo "  Username: patient"
echo "  Password: testpatient123"
echo ""
echo -e "${GREEN}✅ You can now test the login functionality!${NC}"