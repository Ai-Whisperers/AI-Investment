# Waardhaven AutoIndex — AI-Powered Investment Intelligence Platform

🚀 **Professional-grade investment analysis system** combining technical indicators, fundamental analysis, sentiment analysis, and machine learning to generate data-driven investment recommendations with >30% annual return targets.

**NOT A DAY-TRADING PLATFORM**: Designed for serious investors with 3-12 month horizons seeking algorithmic portfolio optimization and risk-adjusted returns.

##  Technology Stack

- **Backend**: FastAPI (Python 3.11+), SQLAlchemy ORM, PostgreSQL, Redis, Celery
- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, TailwindCSS, Recharts
- **Authentication**: JWT tokens with refresh mechanism, Google OAuth integration
- **Market Data**: TwelveData API for daily investment data (NOT real-time trading)
- **News Integration**: MarketAux for investment research and sentiment analysis
- **Infrastructure**: Docker containers, Turborepo monorepo, GitHub Actions CI/CD
- **Deployment**: Render.com (Docker-based with PostgreSQL)

## 🎯 Core Capabilities

### 📊 Investment Intelligence Engine
- **Multi-Signal Analysis**: Aggregates technical, fundamental, sentiment, momentum, and risk signals
- **Weighted Scoring**: Configurable signal weights optimized for long-term investing (40% fundamental, 20% technical)
- **Automated Recommendations**: Buy/sell/hold decisions with confidence scores (0-100)
- **Risk Management**: Automatic stop-loss, position sizing, and portfolio diversification
- **Investment Rationale**: Human-readable explanations for every recommendation

### 📈 Technical Analysis Suite
- **Indicators**: SMA, EMA, RSI, MACD, Bollinger Bands, Stochastic, ATR, OBV, VWAP
- **Pattern Recognition**: Support/resistance levels, trend identification
- **Signal Generation**: Automated buy/sell signals from technical patterns
- **Multi-timeframe Analysis**: Short (1-3mo), Medium (3-12mo), Long (12mo+)

### 💰 Fundamental Analysis
- **Valuation Metrics**: P/E, PEG, P/B, P/S, EV/EBITDA ratios
- **Financial Health**: Debt-to-Equity, Current/Quick ratios, ROE, ROA, ROIC
- **Growth Analysis**: Revenue and earnings growth rates
- **DCF Valuation**: Intrinsic value calculation using discounted cash flows
- **Health Scoring**: Automated financial health assessment (excellent/good/moderate/poor)

### ⚡ Backtesting & Validation
- **Historical Simulation**: Test strategies on years of historical data
- **Performance Metrics**: Sharpe ratio, max drawdown, win rate, alpha/beta
- **Portfolio Management**: Position tracking, rebalancing, transaction costs
- **Strategy Optimization**: Grid search parameter tuning
- **Benchmark Comparison**: S&P 500 relative performance

### 🏢 Asset Classification System
- **Sector Analysis**: 12+ sectors with industry breakdowns
- **ESG Scoring**: Environmental, social, governance ratings
- **Market Cap Categories**: Micro, small, mid, large, mega cap classification
- **Supply Chain Mapping**: Dependency and risk analysis
- **Smart Tagging**: AI, renewable, biotech, fintech, blockchain, etc.

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

## 🔌 API Endpoints (145+ Total)

### 🎯 Investment Intelligence (`/api/v1/investment`)
- `POST /analyze` - Comprehensive investment analysis for any symbol
- `POST /screen` - Screen opportunities based on criteria
- `POST /backtest` - Run historical strategy simulation
- `GET /recommendations/portfolio` - Personalized portfolio recommendations
- `GET /signals/{symbol}` - All signals for a specific asset

### 📊 Technical Analysis (`/api/v1/analysis/technical`)
- `GET /{symbol}` - Complete technical analysis
- `GET /{symbol}/rsi` - RSI indicator with signals
- `GET /{symbol}/macd` - MACD with crossovers
- `GET /{symbol}/bollinger` - Bollinger Bands analysis
- `GET /{symbol}/support-resistance` - Key price levels

### 💼 Fundamental Analysis (`/api/v1/analysis/fundamental`)
- `GET /{symbol}` - Complete fundamental analysis
- `GET /{symbol}/valuation` - Valuation metrics
- `GET /{symbol}/growth` - Growth metrics
- `GET /{symbol}/financial-health` - Health assessment
- `GET /screener/value` - Value stock screening

### 🏷️ Asset Management (`/api/v1/assets`)
- `GET /` - Filter assets by sector/industry/tags/ESG
- `GET /sectors` - Sector analysis with statistics
- `GET /screener/esg` - ESG-focused screening
- `GET /screener/dividend` - Dividend stock screening
- `GET /supply-chain/{symbol}` - Supply chain analysis

### 📈 Signal Detection (`/api/v1/signals`, `/api/v1/momentum`)
- 38+ endpoints for agro-robotics, regulatory, supply chain signals
- 15+ momentum and OSINT tracking endpoints
- 75% signal win rate across 113 routes

## 🆕 Latest Updates (2025-01-23)

### 🧠 Investment Intelligence Layer
- ✅ **Investment Decision Engine**: 750+ lines of sophisticated signal aggregation
- ✅ **Technical Indicators**: Complete suite with 14 indicators
- ✅ **Fundamental Analysis**: 20+ financial metrics and ratios
- ✅ **Backtesting Framework**: Historical validation with performance metrics
- ✅ **API Integration**: 20+ new investment endpoints

### 🏗️ Previous Milestones
- **Asset Classification**: Sector/industry/ESG categorization (2025-01-23)
- **Signal Detection System**: 113 routes with 75% win rate (2025-01-22)
- **Clean Architecture**: SOLID principles implementation (2025-01-19)
- **Test Infrastructure**: 300+ tests with factories (2025-01-21)

## 📊 Platform Metrics

### 🎯 Current Capabilities
- **145+ API Endpoints**: Comprehensive coverage across all investment domains
- **300+ Unit Tests**: 45% code coverage with modular test factories
- **5 Signal Sources**: Technical, fundamental, sentiment, momentum, risk
- **14 Technical Indicators**: Professional-grade analysis tools
- **20+ Fundamental Metrics**: Complete financial health assessment
- **12+ Asset Sectors**: With industry breakdowns and ESG scoring
- **3 Investment Horizons**: Short (1-3mo), Medium (3-12mo), Long (12mo+)
- **Backtesting Engine**: Validate strategies before deployment

### 🚀 Ready for Production
- ✅ Investment Decision Engine operational
- ✅ Technical/Fundamental analysis complete
- ✅ Backtesting and validation framework
- ✅ Risk management and position sizing
- ✅ Asset classification and screening
- ✅ Authentication and security
- ✅ Docker deployment ready
- ✅ CI/CD pipeline configured

### 🔄 Next Phase (Q1 2025)
- 📍 Real-time market data integration
- 📍 Machine learning price predictions
- 📍 Social sentiment analysis pipeline
- 📍 Advanced portfolio optimization (MPT, Black-Litterman)
- 📍 Mobile application development
- 📍 WebSocket real-time updates

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
Last updated: 2025-01-23
