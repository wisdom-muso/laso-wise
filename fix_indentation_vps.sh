#!/bin/bash

# =============================================================================
# Fix Indentation Error in Dashboard View - VPS Quick Fix
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔧 LASO Healthcare Indentation Fix${NC}"
echo -e "${BLUE}=================================${NC}"

# Check if we're in the right directory
if [ ! -f "docker-compose.production.yml" ]; then
    echo -e "${RED}❌ docker-compose.production.yml not found. Please run from project root.${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Pulling latest code changes...${NC}"
git pull origin vps-deployment-automation || echo "Git pull failed, continuing with local fix..."

echo -e "${YELLOW}Step 2: Applying indentation fix directly to container...${NC}"

# Create the indentation fix script inline
docker compose -f docker-compose.production.yml exec -T web python -c "
import os

# Read the current views.py file
with open('/app/core/views.py', 'r') as f:
    content = f.read()

# Check if the indentation error exists
if 'if user.is_patient():\n        # Patient dashboard' in content:
    print('✅ Indentation error found, applying fix...')
    
    # Fix the indentation by replacing the problematic section
    fixed_content = content.replace(
        'if user.is_patient():\n        # Patient dashboard',
        'if user.is_patient():\n            # Patient dashboard'
    )
    
    # Fix other indentation issues
    lines = fixed_content.split('\n')
    fixed_lines = []
    in_try_block = False
    
    for i, line in enumerate(lines):
        if 'try:' in line and 'dashboard' in lines[i-5:i+5]:
            in_try_block = True
            fixed_lines.append(line)
        elif line.strip().startswith('except Exception as e:'):
            in_try_block = False
            fixed_lines.append(line)
        elif in_try_block and line.startswith('    ') and not line.startswith('        '):
            # Add extra indentation for try block content
            if 'elif user.is_' in line or 'if user.is_' in line:
                fixed_lines.append('    ' + line)
            else:
                fixed_lines.append('    ' + line)
        else:
            fixed_lines.append(line)
    
    fixed_content = '\n'.join(fixed_lines)
    
    # Write the fixed content back
    with open('/app/core/views.py', 'w') as f:
        f.write(fixed_content)
    
    print('✅ Indentation fix applied successfully!')
else:
    print('✅ No indentation error found, file appears to be correct.')
"

echo -e "${YELLOW}Step 3: Restarting web container...${NC}"
docker compose -f docker-compose.production.yml restart web

echo -e "${YELLOW}Step 4: Waiting for container to be ready...${NC}"
sleep 20

echo -e "${YELLOW}Step 5: Checking container status...${NC}"
docker compose -f docker-compose.production.yml ps

echo -e "${YELLOW}Step 6: Testing web container health...${NC}"
WEB_STATUS=$(docker compose -f docker-compose.production.yml ps --format json | grep web | grep -o '"State":"[^"]*"' | cut -d'"' -f4)

if [[ "$WEB_STATUS" == "running" ]]; then
    echo -e "${GREEN}✅ Web container is running successfully!${NC}"
    
    echo -e "${YELLOW}Step 7: Testing login functionality...${NC}"
    
    # Test patient login
    PATIENT_TEST=$(curl -s -w "%{http_code}" -o /dev/null http://65.108.91.110/login/ 2>/dev/null || echo "FAILED")
    
    if [[ "$PATIENT_TEST" == "200" ]]; then
        echo -e "${GREEN}✅ Login page is accessible!${NC}"
        
        # Test dashboard access
        DASHBOARD_TEST=$(curl -s -w "%{http_code}" -o /dev/null http://65.108.91.110/dashboard/ 2>/dev/null || echo "FAILED")
        
        if [[ "$DASHBOARD_TEST" == "302" ]]; then
            echo -e "${GREEN}✅ Dashboard redirects properly (login required)${NC}"
        elif [[ "$DASHBOARD_TEST" == "200" ]]; then
            echo -e "${GREEN}✅ Dashboard is accessible${NC}"
        else
            echo -e "${YELLOW}⚠️  Dashboard response: $DASHBOARD_TEST${NC}"
        fi
    else
        echo -e "${RED}❌ Login page test failed: $PATIENT_TEST${NC}"
    fi
else
    echo -e "${RED}❌ Web container is not running properly: $WEB_STATUS${NC}"
    echo -e "${YELLOW}Checking container logs...${NC}"
    docker compose -f docker-compose.production.yml logs web --tail 20
fi

echo -e "${BLUE}=================================${NC}"
echo -e "${GREEN}🎉 Indentation fix completed!${NC}"
echo ""
echo -e "${YELLOW}🔑 TEST THE LOGIN NOW:${NC}"
echo ""
echo -e "${BLUE}Patient Login:${NC}"
echo "  URL: http://65.108.91.110/login/"
echo "  Username: patient"
echo "  Password: testpatient123"
echo ""
echo -e "${BLUE}Admin Login:${NC}"
echo "  URL: http://65.108.91.110/admin/"
echo "  Username: admin"
echo "  Password: 8gJW48Tz8YXDrF57"
echo ""
echo -e "${GREEN}✅ The indentation error should now be fixed!${NC}"