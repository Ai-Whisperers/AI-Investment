# Waardhaven AutoIndex — Production-Ready Investment Portfolio Management System

A comprehensive investment portfolio management platform with automated index creation, strategy optimization, and real-time market data integration.

##  Technology Stack

- **Backend**: FastAPI (Python 3.11+), SQLAlchemy ORM, PostgreSQL, Redis, Celery
- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, TailwindCSS, Recharts
- **Authentication**: JWT tokens with refresh mechanism, Google OAuth integration
- **Market Data**: TwelveData API for professional-grade financial data
- **News Integration**: MarketAux for financial news aggregation
- **Infrastructure**: Docker containers, Turborepo monorepo, GitHub Actions CI/CD
- **Deployment**: Render.com (Docker-based with PostgreSQL)

##  Core Features

### Portfolio Management
- **Automated Index Creation**: Dynamic portfolio construction with multiple weighting strategies
- **Strategy Optimization**: Configurable momentum, market cap, and risk parity weights
- **Performance Analytics**: Real-time Sharpe ratio, Sortino ratio, maximum drawdown
- **Multi-Currency Support**: Automatic exchange rate conversion for global portfolios
- **Benchmark Comparison**: S&P 500 tracking and relative performance analysis

### Technical Capabilities
- **Clean Architecture**: Domain-driven design with separation of concerns
- **Background Processing**: Celery-based async tasks with Redis queue
- **Caching Layer**: Redis caching with automatic invalidation
- **Real-Time Monitoring**: System health indicators and data quality metrics
- **Task Management**: Flower dashboard for background job monitoring
- **Security**: JWT authentication, rate limiting, CORS, security headers

## ️ Architecture

### Backend Structure
```
apps/api/
├── app/
│   ├── core/          # Core infrastructure (database, config, redis, celery)
│   ├── models/        # SQLAlchemy models and Pydantic schemas
│   ├── routers/       # API endpoints (10 router modules)
│   ├── services/      # Business logic (6 service modules)
│   ├── providers/     # External integrations (TwelveData, MarketAux)
│   └── tests/         # Comprehensive test suite (10 test files)
```

### Frontend Structure (Clean Architecture)
```
apps/web/
├── app/
│   ├── core/
│   │   ├── domain/         # Business entities and rules
│   │   ├── application/    # Use cases and business logic
│   │   ├── infrastructure/ # API clients and repositories
│   │   └── presentation/   # React hooks and contexts
│   ├── components/         # Reusable UI components
│   ├── services/          # API service layer
│   └── [pages]/           # Next.js pages (9 routes)
```

##  Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 14+
- Redis (optional for caching/background tasks)
- Docker (optional but recommended)

### Environment Setup
```bash
# Copy environment templates
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env.local
```

**Required API Keys**:
- **TwelveData**: Get from https://twelvedata.com/account/api-keys
- **MarketAux**: Get from https://marketaux.com (optional for news)

### Backend Setup
```bash
cd apps/api

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database (auto-migrations included)
python -m app.db_init

# Optional: Start background workers
celery -A app.core.celery_app worker --loglevel=info  # In new terminal
celery -A app.core.celery_app flower --port=5555      # Monitoring dashboard

# Run API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd apps/web

# Install dependencies
npm install

# Run development server
npm run dev
```

Open http://localhost:3000 in your browser.

### Running Tests
```bash
# Backend tests with coverage
cd apps/api
pytest --cov=app --cov-report=html

# Type checking
cd apps/web
npx tsc --noEmit

# Linting
cd apps/api
ruff check .
```

##  Production Deployment (Render.com)

### Deployment Configuration
The project includes a `render.yaml` for automated deployment:

1. **Backend API**: Docker web service (`apps/api/Dockerfile.api`)
2. **Frontend Web**: Docker web service (`apps/web/Dockerfile.web`)
3. **PostgreSQL**: Managed database instance
4. **Redis**: For caching and background tasks (optional)

### Environment Variables
Configure these in Render dashboard:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key
- `TWELVEDATA_API_KEY`: Market data API key
- `FRONTEND_URL`: CORS allowed origin
- `REDIS_URL`: Redis connection (optional)

##  API Endpoints

### Authentication (`/api/v1/auth`)
- `POST /register` - User registration
- `POST /login` - User login with JWT
- `POST /google` - Google OAuth authentication
- `GET /me` - Get current user info
- `POST /refresh` - Refresh access token
- `POST /logout` - User logout

### Portfolio Management (`/api/v1/index`)
- `GET /` - Portfolio index values with history
- `GET /allocations` - Current asset allocations
- `GET /simulation` - Portfolio simulation with parameters
- `GET /performance` - Performance metrics and analytics

### Strategy Configuration (`/api/v1/strategy`)
- `GET /config` - Get current strategy configuration
- `POST /config` - Update strategy parameters
- `GET /risk-metrics` - Risk analysis and metrics

### Market Data (`/api/v1/benchmark`)
- `GET /sp500` - S&P 500 benchmark data
- `GET /compare` - Portfolio vs benchmark comparison

### System Management (`/api/v1/diagnostics`)
- `GET /health` - System health check
- `GET /data-status` - Data freshness and quality
- `GET /cache-status` - Redis cache statistics

### Background Tasks (`/api/v1/tasks`)
- `POST /refresh` - Trigger data refresh
- `GET /status/{task_id}` - Check task status
- `GET /list` - List all background tasks

### News Integration (`/api/v1/news`)
- `GET /` - Financial news feed
- `GET /sentiment` - Market sentiment analysis

##  Recent Updates

### 2025-01-19 - Clean Architecture Implementation
-  **Frontend Refactoring**: Complete separation of concerns following SOLID principles
-  **Domain Layer**: Pure business entities and rules
-  **Infrastructure Layer**: API clients with dependency injection
-  **Presentation Layer**: React-specific code with custom hooks
-  **Type Safety**: Full TypeScript compliance across all layers

### 2025-01-18 - Authentication & Deployment Fixes
-  **Auth Integration**: Fixed AuthProvider context issues
-  **JWT Implementation**: Complete token refresh mechanism
-  **Deployment Ready**: Render.com configuration verified
-  **CORS Configuration**: Production-ready security settings

### 2025-01-17 - Performance & Infrastructure
-  **Redis Caching**: Full caching layer implementation
-  **Background Tasks**: Celery integration with queues
-  **Database Indexes**: Composite indexes for 50%+ performance gain
-  **Test Suite**: 10 test files with comprehensive coverage

##  Project Status

### Implemented Features (90%+ Complete)
-  User authentication with JWT and OAuth
-  Portfolio index calculation and management
-  Strategy configuration and optimization
-  Market data integration (TwelveData)
-  Financial news aggregation (MarketAux)
-  Performance analytics and risk metrics
-  Background task processing
-  Redis caching layer
-  Clean architecture implementation
-  CI/CD pipeline with GitHub Actions
-  Docker containerization
-  Production deployment on Render

### Pending Enhancements
- ⏳ WebSocket support for real-time updates
- ⏳ Advanced monitoring (Prometheus/Grafana)
- ⏳ Frontend unit tests (Jest/RTL)
- ⏳ E2E testing (Playwright/Cypress)
- ⏳ GraphQL API alternative
- ⏳ Mobile application

##  Documentation

Comprehensive documentation available in `/docs`:
- Architecture guides
- API documentation
- Deployment instructions
- Development workflows
- Testing strategies

##  License

Proprietary - All rights reserved

---

Built with ️ by the Waardhaven team
Last updated: 2025-01-19
