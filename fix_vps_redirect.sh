#!/bin/bash

# =============================================================================
# Complete Redirect Authentication Fix for LASO Healthcare VPS
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔧 LASO Healthcare Redirect Authentication Fix${NC}"
echo -e "${BLUE}=============================================${NC}"

# Check if we're in the right directory
if [ ! -f "docker-compose.production.yml" ]; then
    echo -e "${RED}❌ docker-compose.production.yml not found. Please run from project root.${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Checking container status...${NC}"
docker compose -f docker-compose.production.yml ps

echo -e "${YELLOW}Step 2: Running redirect authentication debug...${NC}"
docker compose -f docker-compose.production.yml exec -T web python /app/debug_redirect_issue.py

echo -e "${YELLOW}Step 3: Applying redirect authentication fixes...${NC}"
docker compose -f docker-compose.production.yml exec -T web python /app/fix_redirect_authentication.py

echo -e "${YELLOW}Step 4: Restarting web container to apply code changes...${NC}"
docker compose -f docker-compose.production.yml restart web

echo -e "${YELLOW}Step 5: Waiting for web container to be ready...${NC}"
sleep 15

echo -e "${YELLOW}Step 6: Testing login functionality...${NC}"

# Test patient login
echo -e "${BLUE}Testing patient login...${NC}"
PATIENT_TEST=$(curl -s -c cookies.txt -b cookies.txt -X POST \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=patient&password=testpatient123" \
    -w "%{http_code}" \
    http://65.108.91.110/login/ || echo "FAILED")

if [[ "$PATIENT_TEST" == *"302"* ]]; then
    echo -e "${GREEN}✅ Patient login successful (redirected)${NC}"
    
    # Follow the redirect
    DASHBOARD_TEST=$(curl -s -b cookies.txt -w "%{http_code}" \
        http://65.108.91.110/dashboard/ || echo "FAILED")
    
    if [[ "$DASHBOARD_TEST" == *"200"* ]]; then
        echo -e "${GREEN}✅ Patient dashboard accessible${NC}"
    else
        echo -e "${RED}❌ Patient dashboard failed: $DASHBOARD_TEST${NC}"
    fi
else
    echo -e "${RED}❌ Patient login failed: $PATIENT_TEST${NC}"
fi

# Test admin login
echo -e "${BLUE}Testing admin login...${NC}"
ADMIN_TEST=$(curl -s -c admin_cookies.txt -b admin_cookies.txt -X POST \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin&password=8gJW48Tz8YXDrF57" \
    -w "%{http_code}" \
    http://65.108.91.110/login/ || echo "FAILED")

if [[ "$ADMIN_TEST" == *"302"* ]]; then
    echo -e "${GREEN}✅ Admin login successful (redirected)${NC}"
    
    # Test admin panel access
    ADMIN_PANEL_TEST=$(curl -s -b admin_cookies.txt -w "%{http_code}" \
        http://65.108.91.110/admin/ || echo "FAILED")
    
    if [[ "$ADMIN_PANEL_TEST" == *"200"* ]]; then
        echo -e "${GREEN}✅ Admin panel accessible${NC}"
    else
        echo -e "${RED}❌ Admin panel failed: $ADMIN_PANEL_TEST${NC}"
    fi
else
    echo -e "${RED}❌ Admin login failed: $ADMIN_TEST${NC}"
fi

# Clean up cookies
rm -f cookies.txt admin_cookies.txt

echo -e "${YELLOW}Step 7: Final verification...${NC}"

# Run the comprehensive test
docker compose -f docker-compose.production.yml exec -T web python /app/test_login_fix.py

echo -e "${BLUE}=============================================${NC}"
echo -e "${GREEN}🎉 Redirect authentication fix completed!${NC}"
echo ""
echo -e "${YELLOW}🔑 LOGIN CREDENTIALS:${NC}"
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
echo -e "${GREEN}✅ Users should now be properly redirected after login!${NC}"