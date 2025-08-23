#!/bin/bash

# Generate SSL certificates for development
# This script creates self-signed certificates for local development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔐 Generating SSL certificates for development...${NC}"

# Create SSL directory if it doesn't exist
mkdir -p nginx/ssl

# Generate private key
echo -e "${YELLOW}Generating private key...${NC}"
openssl genrsa -out nginx/ssl/key.pem 2048

# Generate certificate signing request
echo -e "${YELLOW}Generating certificate signing request...${NC}"
openssl req -new -key nginx/ssl/key.pem -out nginx/ssl/cert.csr -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Generate self-signed certificate
echo -e "${YELLOW}Generating self-signed certificate...${NC}"
openssl x509 -req -days 365 -in nginx/ssl/cert.csr -signkey nginx/ssl/key.pem -out nginx/ssl/cert.pem

# Set proper permissions
chmod 600 nginx/ssl/key.pem
chmod 644 nginx/ssl/cert.pem

# Clean up CSR file
rm nginx/ssl/cert.csr

echo -e "${GREEN}✅ SSL certificates generated successfully!${NC}"
echo -e "${YELLOW}📁 Certificates location: nginx/ssl/${NC}"
echo -e "${YELLOW}🔑 Private key: nginx/ssl/key.pem${NC}"
echo -e "${YELLOW}📜 Certificate: nginx/ssl/cert.pem${NC}"
echo -e "${RED}⚠️  Note: These are self-signed certificates for development only!${NC}"
echo -e "${RED}   For production, use valid SSL certificates from a trusted CA.${NC}"