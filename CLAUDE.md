# CLAUDE.md - AI Assistant Context

## Project Overview
Waardhaven AutoIndex is a production-ready investment portfolio management system with automated index creation, strategy optimization, and real-time market data integration. Currently deployed on Render.com with **84% test pass rate** and **90%+ feature completeness**.

## Tech Stack
- **Backend**: FastAPI (Python 3.11+), SQLAlchemy, PostgreSQL, Redis, Celery
- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS, Recharts
- **Infrastructure**: Docker, Render.com deployment, GitHub Actions CI/CD
- **Package Manager**: npm (standardized across monorepo)
- **Testing**: pytest (backend - 84% pass rate), Jest (frontend - configured)

## Project Structure
```
waardhaven-autoindex/
├── apps/
│   ├── api/                # FastAPI backend
│   │   ├── app/
│   │   │   ├── services/
│   │   │   │   ├── performance_modules/  # Performance calculations
│   │   │   │   ├── strategy_modules/     # Strategy implementations
│   │   │   │   └── news_modules/         # News processing
│   │   │   └── models/
│   │   ├── tests/          # Test suite (84% pass rate)
│   │   │   ├── unit/       # 27/32 tests passing
│   │   │   ├── integration/# 8 integration tests
│   │   │   ├── smoke/      # 12 production health checks
│   │   │   ├── factories/  # Modular test data generators
│   │   │   └── conftest.py # Shared fixtures
│   │   ├── requirements.txt     # Locked dependencies
│   │   ├── requirements.in      # Source dependencies
│   │   ├── requirements-test.txt# Test dependencies
│   │   ├── Makefile            # Dependency management commands
│   │   └── pyproject.toml      # Project configuration
│   └── web/                # Next.js frontend (Clean Architecture)
│       └── app/
│           ├── core/           # Clean Architecture layers
│           │   ├── domain/     # Business entities & use cases
│           │   ├── application/# Application-specific use cases
│           │   ├── infrastructure/# API clients, repositories
│           │   └── presentation/  # React components, hooks
│           ├── services/api/   # Direct API service calls
│           ├── components/     # Shared UI components
│           └── __tests__/      # Frontend tests
├── docs/                   # Comprehensive documentation
├── .github/
│   ├── workflows/         # CI/CD pipelines
│   └── dependabot.yml     # Automated dependency updates
└── turbo.json             # Turborepo configuration
```

## Current Status (2025-01-20)

### 🎯 Test Suite Performance
- **Overall Pass Rate**: 84% (27 of 32 tests passing)
- **Unit Tests**: 27/32 passing
  - Portfolio Model: 9/9 ✅
  - Auth Endpoints: 18/23 (78%)
- **Integration Tests**: 8 tests configured
- **Smoke Tests**: 12 production health checks
- **Coverage**: ~50% (increased from 25-30%)

### ✅ Recent Achievements

#### 1. Dependency Management System
- **Fixed**: All numpy/scipy/pandas version conflicts
- **Dependabot**: Automated weekly updates configured
- **pip-tools**: requirements.in → requirements.txt workflow
- **Makefile**: Streamlined dependency commands
- **CI/CD**: Enhanced caching and retry mechanisms

#### 2. Authentication & Security
- JWT token creation with proper dict parameters
- Added `iat` field for unique tokens
- Google OAuth redirect endpoint
- Password validation (422 status codes)
- User model with `is_active` field
- bcrypt password hashing

#### 3. Database & Testing
- Foreign key constraints for SQLite tests
- SQLite detection for migration skipping
- In-memory test database
- Modular test factories
- Comprehensive fixtures

## Critical Commands
```bash
# Frontend development
cd apps/web && npm run dev

# Backend development  
cd apps/api && uvicorn app.main:app --reload

# Run tests
cd apps/api && python -m pytest tests/unit -v       # Unit tests only
cd apps/api && python -m pytest --cov=app           # With coverage
cd apps/api && python -m pytest tests/integration   # Integration tests

# Dependency management
cd apps/api && make update-deps    # Update dependencies
cd apps/api && make compile-deps   # Compile requirements.txt
cd apps/api && make install        # Install all dependencies

# Type checking & linting
cd apps/web && npx tsc --noEmit
cd apps/api && ruff check .
cd apps/api && black .
```

## Test Infrastructure

### Test Categories
1. **Unit Tests** (32 tests)
   - Fast, isolated component tests
   - Database models, API endpoints, services
   - 84% pass rate

2. **Integration Tests** (8 tests)
   - Cross-component workflows
   - Authentication flows
   - Portfolio management

3. **Smoke Tests** (12 tests)
   - Production health checks
   - API availability
   - Performance monitoring

### Key Test Fixtures
- `test_db_session`: SQLite in-memory database
- `client`: FastAPI test client
- `auth_headers`: JWT authentication headers
- `test_user`: Pre-configured user with password
- `sample_assets`: Market data fixtures

## Dependency Management

### Configuration Files
- `requirements.in`: Source dependencies (human-edited)
- `requirements.txt`: Locked versions (generated)
- `requirements-test.txt`: Test dependencies
- `.github/dependabot.yml`: Automated updates
- `Makefile`: Management commands

### Key Dependencies
```ini
# Production
fastapi>=0.112.0
SQLAlchemy>=2.0.0
pydantic>=2.0.0
redis>=5.0.0
celery>=5.3.0
pandas>=2.0.0
numpy>=1.23.2,<1.28.0  # scipy compatibility
scipy>=1.11.0,<2.0.0

# Testing  
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
factory-boy>=3.3.0
```

## API Endpoints
Base URL: `/api/v1/`

### Authentication (`/auth/*`)
- `POST /register` - User registration ✅
- `POST /login` - User login ✅
- `GET /google` - Google OAuth redirect ✅
- `POST /google` - Google OAuth callback ✅
- `GET /me` - Current user info ✅
- `POST /refresh` - Refresh token ✅
- `POST /logout` - User logout ✅

### Core Functionality
- `/index/*` - Portfolio index operations
- `/benchmark/*` - S&P 500 comparison
- `/strategy/*` - Strategy configuration
- `/portfolio/*` - Portfolio management
- `/tasks/*` - Background task management
- `/diagnostics/*` - System health checks

## Database Models
- **User**: Authentication with `is_active` field
- **Portfolio**: User portfolios with strategies
- **Asset**: Stock/ETF/commodity information
- **Price**: Historical price data
- **IndexValue**: Calculated index values
- **Allocation**: Asset allocation weights

## Environment Variables
```env
# Backend (apps/api/.env)
DATABASE_URL=postgresql://...
SECRET_KEY=<jwt-secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
TWELVEDATA_API_KEY=<api-key>
REDIS_URL=redis://localhost:6379
SKIP_STARTUP_REFRESH=true

# Frontend (apps/web/.env)
NEXT_PUBLIC_API_URL=<api-url>
```

## Recent Code Refactoring (95% Complete)

### Frontend (100% Complete)
- Dashboard: 797 → 173 lines (78% reduction)
- PerformanceChart: 547 → 281 lines (49% reduction)
- Diagnostics: 524 → 90 lines (83% reduction)
- Clean Architecture implementation

### Backend (95% Complete)
- Strategy Service: 633 → 284 lines (55% reduction)
- News Service: 564 → 332 lines (41% reduction)
- Performance Service: 498 → 69 lines (86% reduction)
- All files under 400 lines

## CI/CD Pipeline

### GitHub Actions Workflows
- **Backend Tests**: 84% pass rate ✅
- **Backend Security**: Bandit & Safety scans
- **Backend Code Quality**: Ruff linting
- **Dependency Review**: Automated PR checks
- **Deploy**: Render.com deployment

### Pipeline Features
- Dependency caching
- Parallel job execution
- PostgreSQL & Redis services
- Automatic retries
- Security scanning

## Known Issues & Solutions

### ✅ Resolved Issues
1. **Dependency conflicts** → pip-tools + Dependabot
2. **Test failures** → Fixed auth & model issues
3. **Migration warnings** → SQLite detection
4. **Token generation** → Added `iat` field
5. **Password validation** → 422 status codes

### ⚠️ Remaining Issues (Non-Critical)
1. **Admin endpoints** (404) - Not implemented yet
2. **Rate limiting tests** - Feature not built
3. **Some ruff warnings** - Minor formatting issues
4. **Test report generation** - XML output missing

## Development Workflow
1. Check existing patterns before changes
2. Use existing dependencies (check first!)
3. Follow naming conventions
4. Test with both frontend and API
5. Ensure TypeScript compliance
6. Run linting before commits

## Security Implementation
- JWT authentication with refresh tokens
- bcrypt password hashing
- CORS properly configured
- Security headers middleware
- Input validation with Pydantic
- SQL injection prevention via SQLAlchemy

## Performance Features
- Redis caching layer
- Celery background tasks
- Database query optimization
- Composite indexes on frequent queries
- Connection pooling
- Lazy loading relationships

## Deployment
- **Platform**: Render.com
- **Database**: PostgreSQL
- **Cache**: Redis
- **Workers**: Celery
- **Monitoring**: Health checks
- **SSL**: Automatic HTTPS

## Next Steps
1. Fix remaining 5 test failures (admin routes)
2. Implement rate limiting
3. Add WebSocket support
4. Set up Prometheus monitoring
5. GraphQL API alternative
6. Increase test coverage to 70%+

## Best Practices
- Never commit secrets or API keys
- Always use environment variables
- Test locally before pushing
- Update documentation with changes
- Follow Clean Architecture principles
- Use type hints in Python
- Maintain test coverage above 50%