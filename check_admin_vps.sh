#!/bin/bash

# =============================================================================
# Check Current Admin Credentials on VPS
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔍 Checking Current Admin Credentials${NC}"
echo -e "${BLUE}===================================${NC}"

# Check if containers are running
if ! docker compose -f docker-compose.production.yml ps | grep -q "Up"; then
    echo -e "${RED}❌ Containers are not running. Starting them first...${NC}"
    docker compose -f docker-compose.production.yml up -d
    sleep 30
fi

echo -e "${YELLOW}Running admin credentials check...${NC}"

# Run the check script
docker compose -f docker-compose.production.yml exec -T web python /app/check_current_admin.py

echo -e "${BLUE}===================================${NC}"
echo -e "${GREEN}✅ Admin credentials check complete!${NC}"