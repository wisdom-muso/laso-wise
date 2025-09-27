#!/bin/bash

# =============================================================================
# LASO Healthcare - Quick VPS Setup Script
# Run this script on your VPS at 65.108.91.110
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🏥 LASO Healthcare Management System - Quick VPS Setup${NC}"
echo -e "${BLUE}Target VPS: 65.108.91.110${NC}"
echo ""

# Update system
echo -e "${YELLOW}📦 Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Install required packages
echo -e "${YELLOW}📦 Installing required packages...${NC}"
sudo apt install -y curl git ufw

# Install Docker
echo -e "${YELLOW}🐳 Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo -e "${GREEN}✅ Docker installed successfully${NC}"
else
    echo -e "${GREEN}✅ Docker already installed${NC}"
fi

# Install Docker Compose
echo -e "${YELLOW}🐳 Installing Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✅ Docker Compose installed successfully${NC}"
else
    echo -e "${GREEN}✅ Docker Compose already installed${NC}"
fi

# Configure firewall
echo -e "${YELLOW}🔥 Configuring firewall...${NC}"
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
echo -e "${GREEN}✅ Firewall configured${NC}"

# Clone repository
echo -e "${YELLOW}📥 Cloning LASO Healthcare repository...${NC}"
if [[ ! -d "laso-wise" ]]; then
    git clone https://gitlab.com/wisdomlasome-group/laso-wise.git
    cd laso-wise
    git checkout master
else
    cd laso-wise
    git pull origin master
fi

# Set up environment
echo -e "${YELLOW}⚙️ Setting up environment...${NC}"
cp .env.production .env

# Make deployment script executable
chmod +x deploy.sh

echo ""
echo -e "${GREEN}🎉 Setup completed successfully!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "${YELLOW}1. Review the environment file: nano .env${NC}"
echo -e "${YELLOW}2. Run the deployment: sudo ./deploy.sh${NC}"
echo ""
echo -e "${GREEN}After deployment, your system will be available at:${NC}"
echo -e "${BLUE}   http://65.108.91.110/${NC}"
echo -e "${BLUE}   Admin: http://65.108.91.110/admin/${NC}"
echo -e "${BLUE}   Username: admin${NC}"
echo -e "${BLUE}   Password: 8gJW48Tz8YXDrF57${NC}"
echo ""

# Ask if user wants to run deployment now
read -p "Would you like to run the deployment now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🚀 Starting deployment...${NC}"
    sudo ./deploy.sh
fi