# Quick Start Guide

[← Back to Getting Started](README.md)

## 5-Minute Setup

### 1. Clone & Install
```bash
git clone https://github.com/waardhaven/autoindex.git
cd waardhaven-autoindex
npm install
```

### 2. Environment Setup
```bash
# Backend (.env)
cd apps/api
cp .env.example .env
# Edit .env with your values

# Frontend (.env)
cd ../web
cp .env.example .env
# Set NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Database Setup
```bash
# Start PostgreSQL (Docker)
docker run -d \
  --name waardhaven-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=waardhaven \
  -p 5432:5432 \
  postgres:14

# Initialize database
cd apps/api
python -m app.db_init
python -m app.seed_assets
```

### 4. Start Services
```bash
# Terminal 1: Backend
cd apps/api
uvicorn app.main:app --reload

# Terminal 2: Frontend
cd apps/web
npm run dev

# Terminal 3: Redis (optional)
docker run -d -p 6379:6379 redis:alpine
```

### 5. Access Application
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Default Credentials
```json
{
  "email": "admin@example.com",
  "password": "admin123"
}
```

## Verify Installation
```bash
# Check API health
curl http://localhost:8000/health

# Check database
curl http://localhost:8000/api/v1/diagnostics/database-status
```

## Common Issues

### Database Connection Failed
```bash
# Check DATABASE_URL
export DATABASE_URL="postgresql://postgres:postgres@localhost/waardhaven"
```

### Port Already in Use
```bash
# Change ports in .env
PORT=8001  # API
PORT=3001  # Frontend
```

### Missing Dependencies
```bash
# Backend
cd apps/api && pip install -r requirements.txt

# Frontend
cd apps/web && npm install
```

## Next Steps
- [Full Development Setup](DEVELOPMENT_SETUP.md)
- [Configure Environment](ENVIRONMENT_VARIABLES.md)
- [Explore API](../api-reference/README.md)

---
[← Back to Getting Started](README.md)