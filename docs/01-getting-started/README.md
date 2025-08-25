# Getting Started

## Quick Navigation

### 🚀 [Quick Start](QUICK_START.md)
5-minute setup to run the application locally

### 🔑 [Environment Variables](ENVIRONMENT_VARIABLES.md)
Required configuration and secrets

### 📦 [Dependency Management](DEPENDENCY_MANAGEMENT.md)
Managing Python and Node.js dependencies

## Prerequisites

### Required Software
- Python 3.11+
- Node.js 20+
- PostgreSQL 14+
- Redis 5+
- Git

### Recommended Tools
- Docker Desktop
- VS Code
- Postman/Insomnia
- pgAdmin

## Quick Commands

```bash
# Clone repository
git clone https://github.com/Ai-Whisperers/AI-Investment.git
cd waardhaven-autoindex

# Install dependencies
npm install

# Backend development
cd apps/api
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend development
cd apps/web
npm run dev

# Run tests
cd apps/api
python -m pytest tests/unit -v
```

## Project Structure
```
waardhaven-autoindex/
├── apps/
│   ├── api/            # Backend (FastAPI) - 150+ endpoints
│   │   ├── app/
│   │   │   ├── routers/    # API endpoints
│   │   │   ├── services/   # Business logic
│   │   │   ├── models/     # Database models
│   │   │   └── schemas/    # Pydantic schemas
│   │   └── tests/       # 219 test suite
│   └── web/            # Frontend (Next.js)
│       └── app/
│           ├── dashboard/   # Main application
│           ├── auth/        # Authentication
│           └── core/        # Clean Architecture
├── docs/               # Comprehensive documentation
├── scripts/            # Deployment scripts
└── render.yaml        # Render.com configuration
```

## Next Steps
1. [Set up environment](ENVIRONMENT_VARIABLES.md)
2. [Run locally](QUICK_START.md)
3. [Explore API](../02-api-reference/COMPLETE_API_REFERENCE_V2.md)
4. [Deploy to production](../../QUICK_DEPLOYMENT_STEPS.md)

## Current Status
- **Backend**: 150+ API endpoints, 45% test coverage
- **Frontend**: Dashboard, news feed, monitoring complete
- **Authentication**: Google OAuth fully implemented
- **Deployment**: Ready for Render.com (1-hour deployment)
- **Pending**: API keys configuration

---
[← Main Documentation](../README.md)