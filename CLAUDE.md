# CLAUDE.md - AI Assistant Context

## Project Overview
Waardhaven AutoIndex is an AI-powered investment portfolio management system with automated index creation, strategy optimization, and real-time market data integration. The platform aims to democratize investing by making sophisticated financial analysis accessible to non-specialists through AI-driven insights and cross-source information aggregation. Currently deployed on Render.com with **97.6% test pass rate** and **90%+ feature completeness**.

## Tech Stack
- **Backend**: FastAPI (Python 3.11+), SQLAlchemy, PostgreSQL, Redis, Celery
- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS, Recharts
- **Infrastructure**: Docker, Render.com deployment, GitHub Actions CI/CD
- **Package Manager**: npm (standardized across monorepo)
- **Testing**: pytest (backend - 97.6% pass rate, 42% coverage), Jest (frontend - configured)
- **Data Sources**: TwelveData API, MarketAux News API, Social Media scraping (planned)

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
│   │   ├── tests/          # Test suite (97.6% pass rate)
│   │   │   ├── unit/       # 122/125 tests passing
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
│   └── 05-roadmap/
│       └── MAIN-FEATS.txt  # New feature specifications
├── .github/
│   ├── workflows/         # CI/CD pipelines
│   └── dependabot.yml     # Automated dependency updates
└── turbo.json             # Turborepo configuration
```

## Current Status (2025-01-21)

### 🎯 Test Suite Performance
- **Overall Pass Rate**: 97.6% (122 of 125 tests passing)
- **Unit Tests**: 122/125 passing
  - Portfolio Model: 9/9 ✅
  - Auth Endpoints: 21/23 (1 refresh token failure, 1 OAuth redirect failure)
  - Schema Tests: 21/21 ✅
  - Utils/Security: 17/17 ✅
  - Return Calculator: 21/21 ✅
  - Risk Calculator: 20/20 ✅
  - Weight Calculator: 16/17 (1 constraint application failure)
- **Integration Tests**: 8 tests configured
- **Smoke Tests**: 12 production health checks
- **Coverage**: 42% actual (below required 50% threshold) ⚠️

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
1. **Unit Tests** (125 tests)
   - Fast, isolated component tests
   - Database models, API endpoints, services
   - 97.6% pass rate (122/125 passing)

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

### GitHub Actions Workflows (Last Run: 2025-01-20)
- **Backend Tests**: ❌ Failed (3 test failures + coverage 42% < 50%)
- **Backend Security**: ❌ Failed (Bandit exit code 2)
- **Backend Code Quality**: ❌ Failed (21 ruff violations remaining)
- **Quality Gates**: ❌ Failed (Blocked by test failures)
- **Deploy**: ❌ Failed (Blocked by quality gates)
- **Dependency Review**: ✅ Passing

### Pipeline Features
- Dependency caching
- Parallel job execution
- PostgreSQL & Redis services
- Automatic retries
- Security scanning

## Known Issues & Solutions

### ✅ Resolved Issues
1. **Dependency conflicts** → pip-tools + Dependabot
2. **Test failures** → Fixed auth, model, schema, utils, and most service tests
3. **Migration warnings** → SQLite detection
4. **Token generation** → Added `iat` field
5. **Password validation** → 422 status codes
6. **Schema validation** → Fixed for Pydantic v2
7. **Security utils** → Fixed timezone issues in token tests
8. **Return calculator** → Fixed cumulative return calculations

### 🚨 Critical Issues (URGENT - Blocking Deployment)

#### Test Failures (3)
1. **test_apply_weight_constraints** (`tests/unit/services/test_weight_calculator.py:105`)
   - Mathematical impossibility: 2 assets cannot satisfy max_weight=0.40
   - Returns 0.5 each, violating constraint
   
2. **test_refresh_token** (`tests/unit/routers/test_auth.py:171`)
   - Tokens identical due to same timestamp
   - Needs UUID for uniqueness
   
3. **test_google_oauth_redirect** (`tests/unit/routers/test_auth.py:194`)
   - Using Response instead of RedirectResponse
   - Status code mismatch

#### Pipeline Issues
- **Coverage**: 42% (need 50%) - 8% gap
- **Ruff**: 21 manual fixes needed (2074 auto-fixed)
- **Security**: Bandit configuration broken

### ⚠️ Non-Critical Issues
1. **Admin endpoints** (Skipped) - Not implemented yet
2. **Rate limiting tests** (Skipped) - Feature not built
3. **Test report generation** - `test-results.xml` not created

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

## Urgent Tasks (24-Hour Sprint)

### Hour 1-4: Fix Failing Tests
1. **Weight Constraint** - Implement dynamic min_weight adjustment
2. **Token Refresh** - Add UUID to token generation
3. **OAuth Redirect** - Use RedirectResponse class

### Hour 5-8: Increase Coverage (42% → 50%)
1. Write 10 tests for news_modules (~3% gain)
2. Write 5 tests for strategy_modules (~2% gain)
3. Write 5 tests for error cases (~3% gain)

### Hour 9-12: Code Quality
1. Fix 21 remaining ruff violations
2. Fix Bandit security configuration
3. Run full test suite verification

## Planned Features (from OVERALL-FEATS.txt)
### Core Platform Features
1. **Asset Classification System**
   - 12+ sector categories with metadata
   - Supply chain dependency mapping
   - ESG scores and patent portfolios

2. **AI Agent Architecture**
   - **YouTube Agent**: Auto-transcription, credibility scoring
   - **Reddit Agent**: Sentiment analysis, trend detection
   - **TikTok Agent**: FinTok processing, viral tracking
   - Cross-source verification pipeline

3. **Intelligence Layer**
   - Multi-modal analysis (text, video, audio, numerical)
   - Pattern recognition across sources
   - Anomaly detection and opportunity scoring
   - Google-like financial search indexing

4. **User Experience**
   - AI chatbot for investment guidance
   - Real-time news feed with relevance ranking
   - Portfolio simulation and education
   - No high-frequency trading (mid-long term focus)

5. **Data Processing Stack**
   - Kafka/RabbitMQ for streaming
   - Apache Spark for batch processing
   - TimescaleDB for time-series
   - Elasticsearch for search

## Development Phases

### Phase 1: Stabilization (Current - Critical)
- Fix 3 failing tests
- Achieve 50% test coverage
- Restore CI/CD pipeline
- Deploy to production

### Phase 2: Core Enhancement (Weeks 3-4)
- Asset classification system
- Enhanced data analysis
- Fundamental/technical analysis

### Phase 3: AI Intelligence (Weeks 5-6)
- Cross-source data fusion
- Financial search indexing
- Opportunity detection

### Phase 4: Social Integration (Weeks 7-8)
- YouTube/Reddit/TikTok agents
- Sentiment analysis pipeline
- Credibility scoring system

### Phase 5: UX Polish (Weeks 9-10)
- AI chatbot enhancement
- Mobile responsiveness
- Educational content

## Documentation URLs (Quick Reference)

### Core Technologies
- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy 2.0**: https://docs.sqlalchemy.org/en/20/
- **Pydantic v2**: https://docs.pydantic.dev/latest/
- **Next.js 14**: https://nextjs.org/docs
- **React 18**: https://react.dev/reference/react
- **TypeScript**: https://www.typescriptlang.org/docs/

### Infrastructure & Deployment
- **Docker**: https://docs.docker.com/
- **Render.com**: https://docs.render.com/
- **GitHub Actions**: https://docs.github.com/en/actions
- **PostgreSQL**: https://www.postgresql.org/docs/current/
- **Redis**: https://redis.io/docs/latest/

### Testing & Quality
- **pytest**: https://docs.pytest.org/en/stable/
- **Jest**: https://jestjs.io/docs/getting-started
- **Ruff**: https://docs.astral.sh/ruff/
- **Bandit**: https://bandit.readthedocs.io/en/latest/
- **Coverage.py**: https://coverage.readthedocs.io/

### Data Sources & APIs
- **TwelveData API**: https://twelvedata.com/docs
- **MarketAux News API**: https://www.marketaux.com/documentation
- **Celery**: https://docs.celeryq.dev/en/stable/
- **Recharts**: https://recharts.org/en-US/api

### Package Management
- **pip-tools**: https://pip-tools.readthedocs.io/en/latest/
- **npm**: https://docs.npmjs.com/
- **Turborepo**: https://turbo.build/repo/docs
- **Dependabot**: https://docs.github.com/en/code-security/dependabot

### UI & Styling
- **Tailwind CSS**: https://tailwindcss.com/docs
- **shadcn/ui**: https://ui.shadcn.com/docs
- **Radix UI**: https://www.radix-ui.com/primitives/docs

## Best Practices
- Never commit secrets or API keys
- Always use environment variables
- Test locally before pushing
- Update documentation with changes
- Follow Clean Architecture principles
- Use type hints in Python
- Maintain test coverage above 50%