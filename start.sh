#!/bin/bash

set -e

echo "🚀 Starting Smartbook Full Stack..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Creating .env from .env.example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}⚠️  Please edit .env with your configuration${NC}"
    else
        echo -e "${RED}❌ Error: .env.example not found${NC}"
        exit 1
    fi
fi

# Check if frontend/.env exists
if [ ! -f frontend/.env ]; then
    echo -e "${YELLOW}📝 Creating frontend/.env...${NC}"
    if [ -f frontend/.env.example ]; then
        cp frontend/.env.example frontend/.env
    fi
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Docker is not running${NC}"
    echo "Please start Docker and try again"
    exit 1
fi

echo -e "${GREEN}🐳 Building and starting Docker containers...${NC}"
echo "This may take a few minutes on first run..."
echo ""

# Build and start services
docker-compose up --build -d

# Wait for services to be healthy
echo ""
echo -e "${GREEN}⏳ Waiting for services to be ready...${NC}"
sleep 5

# Check backend health
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is ready${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}❌ Backend failed to start${NC}"
    echo "Check logs with: docker-compose logs backend"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Smartbook is running!${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}📱 Guest Portal:${NC}     http://localhost:3000"
echo -e "${GREEN}🖥️  Admin Dashboard:${NC}  http://localhost:3001"
echo -e "${GREEN}🔧 Backend API:${NC}      http://localhost:8000"
echo -e "${GREEN}📊 API Docs:${NC}         http://localhost:8000/api/docs"
echo -e "${GREEN}🗄️  Database:${NC}         localhost:5432"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Useful commands:"
echo "  ${GREEN}docker-compose logs -f${NC}          View all logs"
echo "  ${GREEN}docker-compose logs -f backend${NC}  View backend logs"
echo "  ${GREEN}docker-compose down${NC}             Stop all services"
echo "  ${GREEN}docker-compose restart${NC}          Restart all services"
echo ""
