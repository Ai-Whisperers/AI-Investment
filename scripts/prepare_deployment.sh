#!/bin/bash

# Prepare Deployment Script for Render.com
# This script helps prepare the application for deployment

echo "==========================================="
echo "Waardhaven AutoIndex - Deployment Preparation"
echo "==========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the correct directory
if [ ! -f "package.json" ] || [ ! -d "apps" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    exit 1
fi

echo -e "\n${GREEN}Step 1: Environment Variables Check${NC}"
echo "Please ensure you have the following environment variables configured in Render.com:"
echo ""
echo "Core Configuration:"
echo "  - SECRET_KEY (Generate with: openssl rand -hex 32)"
echo "  - DATABASE_URL (Provided by Render)"
echo "  - REDIS_URL (If using Redis)"
echo ""
echo "API Keys - Data Sources:"
echo "  - TWELVEDATA_API_KEY"
echo "  - MARKETAUX_API_KEY"
echo "  - REDDIT_CLIENT_ID"
echo "  - REDDIT_CLIENT_SECRET"
echo "  - YOUTUBE_API_KEY"
echo ""
echo "Google OAuth:"
echo "  - GOOGLE_CLIENT_ID"
echo "  - GOOGLE_CLIENT_SECRET"
echo "  - GOOGLE_REDIRECT_URI"
echo ""
echo "Notifications:"
echo "  - DISCORD_WEBHOOK"
echo ""
echo "Frontend:"
echo "  - FRONTEND_URL"
echo ""

read -p "Have you configured all required environment variables in Render? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Please configure environment variables in Render dashboard before continuing.${NC}"
    echo "Documentation: docs/DEPLOYMENT_CONFIGURATION.md"
    exit 1
fi

echo -e "\n${GREEN}Step 2: Build Commands for Render${NC}"
echo "Configure these in your Render services:"
echo ""
echo "Backend Service (FastAPI):"
echo "  Build Command: cd apps/api && pip install -r requirements.txt"
echo "  Start Command: cd apps/api && uvicorn app.main:app --host 0.0.0.0 --port \$PORT"
echo "  Health Check Path: /health"
echo ""
echo "Frontend Service (Next.js):"
echo "  Build Command: cd apps/web && npm install && npm run build"
echo "  Start Command: cd apps/web && npm start"
echo ""

echo -e "\n${GREEN}Step 3: Database Migration Commands${NC}"
echo "After deployment, run these commands in Render shell:"
echo ""
echo "cd apps/api"
echo "alembic upgrade head"
echo ""

echo -e "\n${GREEN}Step 4: Test Endpoints${NC}"
echo "After deployment, test these endpoints:"
echo ""
echo "1. Health Check: https://your-api.onrender.com/health"
echo "2. API Docs: https://your-api.onrender.com/docs"
echo "3. Frontend: https://your-frontend.onrender.com"
echo ""

echo -e "\n${GREEN}Step 5: GitHub Actions Secrets${NC}"
echo "Add these secrets to your GitHub repository:"
echo ""
echo "  - RENDER_API_KEY"
echo "  - RENDER_SERVICE_ID"
echo ""

echo -e "\n${GREEN}Deployment Checklist:${NC}"
echo "[ ] Environment variables configured in Render"
echo "[ ] Database URL configured"
echo "[ ] Redis URL configured (if using)"
echo "[ ] API keys added"
echo "[ ] Google OAuth configured"
echo "[ ] Discord webhook configured"
echo "[ ] Build commands configured"
echo "[ ] Health check path set"
echo "[ ] Custom domain configured (optional)"
echo "[ ] SSL certificate enabled"
echo ""

echo -e "${GREEN}Ready for deployment!${NC}"
echo "Next steps:"
echo "1. Push your code to GitHub"
echo "2. Connect your GitHub repo to Render"
echo "3. Deploy the services"
echo "4. Run database migrations"
echo "5. Test all endpoints"
echo ""
echo "For detailed instructions, see: docs/DEPLOYMENT_GUIDE_2025.md"