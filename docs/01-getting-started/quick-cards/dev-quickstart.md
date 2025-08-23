---
title: Developer Quick Start
category: Quick Reference
priority: 1
status: stable
last-updated: 2025-01-19
owner: development-team
---

#  Developer Quick Start Card

##  5-Minute Setup
```bash
# 1. Clone & Install
git clone https://github.com/waardhaven/autoindex.git
cd waardhaven-autoindex
npm install

# 2. Start PostgreSQL & Redis
docker-compose up -d

# 3. Setup Backend
cd apps/api
cp .env.example .env
pip install -r requirements.txt
python -m app.db_init
python -m app.seed_assets

# 4. Setup Frontend
cd ../web
cp .env.example .env
npm install

# 5. Start Everything
npm run dev  # From root directory
```

##  Essential Commands
```bash
# Development
npm run dev              # Start all services
npm run dev:api          # Backend only
npm run dev:web          # Frontend only

# Testing
npm test                 # Run all tests
npm run test:api         # Backend tests
npm run test:web         # Frontend tests
npm run test:coverage    # Coverage report

# Database
npm run db:migrate       # Run migrations
npm run db:seed          # Seed data
npm run db:reset         # Reset database

# Code Quality
npm run lint             # Lint all code
npm run format           # Format code
npm run typecheck        # TypeScript check
```

##  Key Files & Locations
```
apps/api/
├── app/main.py          # FastAPI entry
├── app/routers/         # API endpoints
├── app/services/        # Business logic
└── .env                 # Backend config

apps/web/
├── app/page.tsx         # Homepage
├── app/dashboard/       # Main app
├── app/services/api/    # API client
└── .env                 # Frontend config
```

##  Environment Variables
```bash
# Backend (.env)
DATABASE_URL=postgresql://postgres:postgres@localhost/waardhaven
SECRET_KEY=your-secret-key-here
TWELVEDATA_API_KEY=your-api-key
REDIS_URL=redis://localhost:6379

# Frontend (.env)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

##  Access Points
| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | Web application |
| API | http://localhost:8000 | Backend API |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Redis | localhost:6379 | Cache |
| PostgreSQL | localhost:5432 | Database |

##  Common Issues
| Problem | Solution |
|---------|----------|
| Port in use | Change PORT in .env |
| DB connection failed | Check DATABASE_URL |
| Missing dependencies | `pip install -r requirements.txt` |
| TypeScript errors | `npm run typecheck` |

##  Next Steps
1. [Read Architecture](../../03-implementation/architecture/system-design.md)
2. [Explore API](../../02-api-reference/README.md)
3. [Check TODOs](../../05-roadmap/quick-cards/todo-summary.md)
4. [Join Sprint Planning](../../05-roadmap/quick-cards/sprint-plan.md)

---
*Need help? Check [Troubleshooting](troubleshooting.md) or ask in #dev-help*