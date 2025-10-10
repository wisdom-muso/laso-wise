#!/bin/bash

# =============================================================================
# Run Login Debug Script on VPS
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔍 Running Login Debug Diagnostics${NC}"
echo -e "${BLUE}=================================${NC}"

# Check if containers are running
if ! docker compose -f docker-compose.production.yml ps | grep -q "Up"; then
    echo -e "${RED}❌ Containers are not running. Starting them first...${NC}"
    docker compose -f docker-compose.production.yml up -d
    sleep 30
fi

echo -e "${YELLOW}Running diagnostic script in web container...${NC}"

# Copy the debug script to the container and run it
docker compose -f docker-compose.production.yml exec -T web python /app/debug_login_issue.py

echo -e "${BLUE}=================================${NC}"
echo -e "${GREEN}✅ Diagnostic complete!${NC}"