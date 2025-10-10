#!/bin/bash

# =============================================================================
# Complete Database Reset and User Recreation for LASO Healthcare
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔄 LASO Healthcare Complete Database Reset${NC}"
echo -e "${BLUE}=========================================${NC}"

# Check if we're in the right directory
if [ ! -f "docker-compose.production.yml" ]; then
    echo -e "${RED}❌ docker-compose.production.yml not found. Please run from project root.${NC}"
    exit 1
fi

echo -e "${YELLOW}⚠️  WARNING: This will completely reset the database and all users!${NC}"
echo -e "${YELLOW}This includes deleting ALL existing user accounts and data.${NC}"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Operation cancelled."
    exit 1
fi

echo -e "${YELLOW}Step 1: Stopping all containers...${NC}"
docker compose -f docker-compose.production.yml down

echo -e "${YELLOW}Step 2: Removing database volume to ensure clean state...${NC}"
docker volume rm laso-wise_postgres_data || echo "Volume doesn't exist or already removed"

echo -e "${YELLOW}Step 3: Rebuilding containers...${NC}"
docker compose -f docker-compose.production.yml build --no-cache

echo -e "${YELLOW}Step 4: Starting containers...${NC}"
docker compose -f docker-compose.production.yml up -d

echo -e "${YELLOW}Step 5: Waiting for database to be ready...${NC}"
sleep 45

echo -e "${YELLOW}Step 6: Running fresh database migrations...${NC}"
docker compose -f docker-compose.production.yml exec -T web python manage.py migrate --run-syncdb

echo -e "${YELLOW}Step 7: Collecting static files...${NC}"
docker compose -f docker-compose.production.yml exec -T web python manage.py collectstatic --noinput

echo -e "${YELLOW}Step 8: Running complete database and user reset...${NC}"
docker compose -f docker-compose.production.yml exec -T web python /app/reset_database_and_users.py

echo -e "${YELLOW}Step 9: Final verification...${NC}"

# Test the new admin credentials
echo -e "${BLUE}Testing new admin credentials...${NC}"
ADMIN_TEST=$(docker compose -f docker-compose.production.yml exec -T web python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laso.settings')
django.setup()
from django.contrib.auth import authenticate
user = authenticate(username='admin', password='8gJW48Tz8YXDrF57')
print('SUCCESS' if user and user.is_superuser else 'FAILED')
")

if [[ "$ADMIN_TEST" == *"SUCCESS"* ]]; then
    echo -e "${GREEN}✅ New admin credentials work perfectly!${NC}"
else
    echo -e "${RED}❌ New admin credentials failed!${NC}"
    exit 1
fi

# Test the new patient credentials
echo -e "${BLUE}Testing new patient credentials...${NC}"
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
    echo -e "${GREEN}✅ New patient credentials work perfectly!${NC}"
else
    echo -e "${RED}❌ New patient credentials failed!${NC}"
fi

# Test that old credentials no longer work
echo -e "${BLUE}Verifying old credentials are disabled...${NC}"
OLD_TEST=$(docker compose -f docker-compose.production.yml exec -T web python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laso.settings')
django.setup()
from django.contrib.auth import authenticate
old_passwords = ['admin123', 'admin', 'password', 'laso123', 'healthcare123']
for pwd in old_passwords:
    user = authenticate(username='admin', password=pwd)
    if user:
        print(f'OLD_PASSWORD_WORKS: {pwd}')
        break
else:
    print('OLD_PASSWORDS_DISABLED')
")

if [[ "$OLD_TEST" == *"OLD_PASSWORDS_DISABLED"* ]]; then
    echo -e "${GREEN}✅ Old credentials are properly disabled!${NC}"
else
    echo -e "${RED}⚠️  Warning: Some old credentials might still work: $OLD_TEST${NC}"
fi

echo -e "${YELLOW}Step 10: Checking service status...${NC}"
docker compose -f docker-compose.production.yml ps

echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}🎉 Database reset completed successfully!${NC}"
echo ""
echo -e "${YELLOW}🔑 NEW LOGIN CREDENTIALS:${NC}"
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
echo -e "${GREEN}✅ The old admin credentials should no longer work!${NC}"
echo -e "${GREEN}✅ You can now test the login functionality with the new credentials.${NC}"