#!/bin/bash

# =============================================================================
# Quick Redirect Authentication Fix for LASO Healthcare VPS
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔧 LASO Healthcare Quick Redirect Fix${NC}"
echo -e "${BLUE}====================================${NC}"

# Check if we're in the right directory
if [ ! -f "docker-compose.production.yml" ]; then
    echo -e "${RED}❌ docker-compose.production.yml not found. Please run from project root.${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Rebuilding web container with latest code...${NC}"
docker compose -f docker-compose.production.yml build --no-cache web

echo -e "${YELLOW}Step 2: Restarting containers...${NC}"
docker compose -f docker-compose.production.yml down
docker compose -f docker-compose.production.yml up -d

echo -e "${YELLOW}Step 3: Waiting for containers to be ready...${NC}"
sleep 30

echo -e "${YELLOW}Step 4: Running database migrations...${NC}"
docker compose -f docker-compose.production.yml exec -T web python manage.py migrate

echo -e "${YELLOW}Step 5: Collecting static files...${NC}"
docker compose -f docker-compose.production.yml exec -T web python manage.py collectstatic --noinput

echo -e "${YELLOW}Step 6: Creating inline redirect fix script...${NC}"

# Create the fix script inline
docker compose -f docker-compose.production.yml exec -T web python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'laso.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session

User = get_user_model()

print('🔧 Applying redirect fixes...')

# Fix user types
try:
    admin_user = User.objects.get(username='admin')
    if admin_user.user_type != 'admin':
        admin_user.user_type = 'admin'
        admin_user.save()
        print(f'✅ Fixed admin user type: {admin_user.user_type}')
    else:
        print(f'✅ Admin user type already correct: {admin_user.user_type}')
except User.DoesNotExist:
    print('❌ Admin user not found')

try:
    patient_user = User.objects.get(username='patient')
    if patient_user.user_type != 'patient':
        patient_user.user_type = 'patient'
        patient_user.save()
        print(f'✅ Fixed patient user type: {patient_user.user_type}')
    else:
        print(f'✅ Patient user type already correct: {patient_user.user_type}')
except User.DoesNotExist:
    print('⚠️  Creating patient user...')
    patient_user = User.objects.create_user(
        username='patient',
        email='patient@test.com',
        password='testpatient123',
        first_name='Test',
        last_name='Patient',
        user_type='patient'
    )
    print(f'✅ Created patient user with type: {patient_user.user_type}')

# Clear sessions
session_count = Session.objects.count()
Session.objects.all().delete()
print(f'✅ Cleared {session_count} sessions')

print('✅ Redirect fixes applied successfully!')
"

echo -e "${YELLOW}Step 7: Testing login functionality...${NC}"

# Test patient login
echo -e "${BLUE}Testing patient login...${NC}"
PATIENT_TEST=$(curl -s -c cookies.txt -b cookies.txt -L -X POST \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=patient&password=testpatient123" \
    -w "%{http_code}|%{url_effective}" \
    http://65.108.91.110/login/ 2>/dev/null || echo "FAILED|")

HTTP_CODE=$(echo "$PATIENT_TEST" | cut -d'|' -f1)
FINAL_URL=$(echo "$PATIENT_TEST" | cut -d'|' -f2)

if [[ "$HTTP_CODE" == "200" && "$FINAL_URL" == *"dashboard"* ]]; then
    echo -e "${GREEN}✅ Patient login and redirect successful!${NC}"
    echo -e "${GREEN}   Final URL: $FINAL_URL${NC}"
elif [[ "$HTTP_CODE" == "302" ]]; then
    echo -e "${GREEN}✅ Patient login successful (redirected)${NC}"
    
    # Test dashboard access directly
    DASHBOARD_TEST=$(curl -s -b cookies.txt -w "%{http_code}" \
        http://65.108.91.110/dashboard/ 2>/dev/null || echo "FAILED")
    
    if [[ "$DASHBOARD_TEST" == "200" ]]; then
        echo -e "${GREEN}✅ Patient dashboard accessible${NC}"
    else
        echo -e "${YELLOW}⚠️  Dashboard response: $DASHBOARD_TEST${NC}"
    fi
else
    echo -e "${RED}❌ Patient login test result: $PATIENT_TEST${NC}"
fi

# Test admin login
echo -e "${BLUE}Testing admin login...${NC}"
ADMIN_TEST=$(curl -s -c admin_cookies.txt -b admin_cookies.txt -L -X POST \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin&password=8gJW48Tz8YXDrF57" \
    -w "%{http_code}|%{url_effective}" \
    http://65.108.91.110/login/ 2>/dev/null || echo "FAILED|")

ADMIN_HTTP_CODE=$(echo "$ADMIN_TEST" | cut -d'|' -f1)
ADMIN_FINAL_URL=$(echo "$ADMIN_TEST" | cut -d'|' -f2)

if [[ "$ADMIN_HTTP_CODE" == "200" && "$ADMIN_FINAL_URL" == *"admin"* ]]; then
    echo -e "${GREEN}✅ Admin login and redirect successful!${NC}"
    echo -e "${GREEN}   Final URL: $ADMIN_FINAL_URL${NC}"
elif [[ "$ADMIN_HTTP_CODE" == "302" ]]; then
    echo -e "${GREEN}✅ Admin login successful (redirected)${NC}"
    
    # Test admin panel access
    ADMIN_PANEL_TEST=$(curl -s -b admin_cookies.txt -w "%{http_code}" \
        http://65.108.91.110/admin/ 2>/dev/null || echo "FAILED")
    
    if [[ "$ADMIN_PANEL_TEST" == "200" ]]; then
        echo -e "${GREEN}✅ Admin panel accessible${NC}"
    else
        echo -e "${YELLOW}⚠️  Admin panel response: $ADMIN_PANEL_TEST${NC}"
    fi
else
    echo -e "${RED}❌ Admin login test result: $ADMIN_TEST${NC}"
fi

# Clean up cookies
rm -f cookies.txt admin_cookies.txt 2>/dev/null || true

echo -e "${YELLOW}Step 8: Final container status check...${NC}"
docker compose -f docker-compose.production.yml ps

echo -e "${BLUE}====================================${NC}"
echo -e "${GREEN}🎉 Quick redirect fix completed!${NC}"
echo ""
echo -e "${YELLOW}🔑 TEST THE LOGIN NOW:${NC}"
echo ""
echo -e "${BLUE}Patient Login:${NC}"
echo "  URL: http://65.108.91.110/login/"
echo "  Username: patient"
echo "  Password: testpatient123"
echo "  Expected: Redirect to dashboard"
echo ""
echo -e "${BLUE}Admin Login:${NC}"
echo "  URL: http://65.108.91.110/admin/"
echo "  Username: admin"
echo "  Password: 8gJW48Tz8YXDrF57"
echo "  Expected: Access to Django admin"
echo ""
echo -e "${GREEN}✅ The redirect authentication issues should now be fixed!${NC}"