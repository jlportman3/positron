#!/bin/bash

# Positron GAM Management System - Setup Verification Script

echo "========================================="
echo "Positron GAM Setup Verification"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check functions
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1 (missing)"
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1/"
        return 0
    else
        echo -e "${RED}✗${NC} $1/ (missing)"
        return 1
    fi
}

# Check Docker
echo "Checking Docker..."
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker is installed"
    docker --version
else
    echo -e "${RED}✗${NC} Docker is not installed"
fi

if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker Compose is installed"
    docker-compose --version
else
    echo -e "${RED}✗${NC} Docker Compose is not installed"
fi
echo ""

# Check project structure
echo "Checking project structure..."

# Backend
check_dir "backend"
check_dir "backend/app"
check_dir "backend/app/api"
check_dir "backend/app/models"
check_dir "backend/app/services"
check_dir "backend/app/utils"
check_dir "backend/alembic"

check_file "backend/app/main.py"
check_file "backend/app/config.py"
check_file "backend/app/database.py"
check_file "backend/requirements.txt"
check_file "backend/Dockerfile.dev"
check_file "backend/alembic.ini"

echo ""

# Frontend
check_dir "frontend"
check_dir "frontend/src"
check_dir "frontend/src/components"
check_dir "frontend/src/services"
check_dir "frontend/src/types"

check_file "frontend/src/main.tsx"
check_file "frontend/src/App.tsx"
check_file "frontend/package.json"
check_file "frontend/vite.config.ts"
check_file "frontend/Dockerfile.dev"

echo ""

# Configuration
echo "Checking configuration files..."
check_file ".env"
check_file ".env.example"
check_file "docker-compose.dev.yml"

echo ""

# Documentation
echo "Checking documentation..."
check_file "README.md"
check_file "QUICKSTART.md"
check_file "DEPLOYMENT.md"
check_file "PROJECT_STATUS.md"
check_file "implementation_plan.md"

echo ""

# Check ports
echo "Checking port availability..."
for port in 5433 6380 8001 3001; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠${NC} Port $port is in use"
    else
        echo -e "${GREEN}✓${NC} Port $port is available"
    fi
done

echo ""
echo "========================================="
echo "Verification Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Review .env file and update if needed"
echo "2. Run: docker-compose -f docker-compose.dev.yml up -d"
echo "3. Run: docker-compose -f docker-compose.dev.yml exec positron_backend alembic upgrade head"
echo "4. Access frontend at http://localhost:3001"
echo "5. Access API docs at http://localhost:8001/docs"
echo ""
echo "For detailed instructions, see QUICKSTART.md"
echo ""
