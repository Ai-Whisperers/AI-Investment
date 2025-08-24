# Waardhaven AutoIndex - Complete Module Index
*Last Updated: 2025-01-24*

## 📁 Project Structure Overview

```
waardhaven-autoindex/
├── apps/
│   ├── api/                 # FastAPI backend
│   └── web/                 # Next.js frontend
├── docs/                    # Documentation
├── .github/                 # CI/CD workflows
└── [config files]          # Project configuration
```

## 🔧 Backend Modules (`apps/api/app/`)

### Core Infrastructure (`core/`)
- **config.py** - Application configuration and settings
- **database.py** - Database connection and session management
- **auth.py** - Authentication utilities and JWT handling

### Database Models (`models/`)
| Model | Purpose | Key Fields |
|-------|---------|------------|
| **signals.py** | Extreme alpha signal tracking | ticker, confidence, expected_return, pattern_stack |
| **user.py** | User authentication | email, hashed_password, is_active |
| **portfolio.py** | Portfolio management | user_id, name, strategy_config |
| **asset.py** | Asset information | symbol, name, exchange, market_cap |
| **strategy.py** | Strategy configuration | risk_metrics, market_cap_data |
| **index.py** | Index values and allocations | portfolio_id, value, timestamp |
| **news.py** | News data storage | title, content, sentiment, entities |

### Service Layer (`services/`)

#### 🎯 Core Detection Services
- **alpha_detection.py** - Multi-layer pattern recognition for >30% moves
- **signal_processor.py** - Kelly Criterion position sizing and risk management
- **extreme_backtest.py** - Historical validation (GME, AMC, NVDA)
- **meme_velocity.py** - Viral stock detection and velocity tracking

#### 📊 Analysis Services
- **technical_indicators.py** - RSI, MACD, Bollinger Bands, support/resistance
- **fundamental_analysis.py** - P/E, P/B, DCF valuation, financial health
- **investment_engine.py** - Investment decision aggregation
- **backtesting.py** - Strategy backtesting framework

#### 🌐 Data Collection (`collectors/`)
- **zero_cost_collector.py** - Free tier API orchestration
- **reddit_collector.py** - Reddit/WSB signal extraction
- **youtube_collector.py** - YouTube video analysis
- **chan_collector.py** - 4chan /biz/ monitoring
- **twitter_collector.py** - Twitter sentiment tracking
- **discord_collector.py** - Discord server monitoring
- **zero_cost_orchestrator.py** - Collection scheduling
- **run_collection.py** - Main collection entry point

#### 📈 Market Data (`market_data/`)
- **twelvedata_client.py** - TwelveData API integration
- **market_cache.py** - Redis caching layer
- **rate_limiter.py** - API rate limiting
- **data_transformer.py** - Data normalization

#### 📰 News Processing (`news_modules/`)
- **news_processor.py** - News data processing pipeline
- **sentiment_analyzer.py** - Sentiment analysis
- **entity_extractor.py** - Named entity recognition
- **news_aggregator.py** - Multi-source aggregation

#### 🔍 OSINT Tracking (`osint/`)
- **osint_tracker.py** - Open source intelligence tracking
- **signal_fusion.py** - Multi-source signal fusion
- **entity_resolver.py** - Entity disambiguation
- **data_aggregator.py** - Data aggregation pipeline
- **api_manager.py** - API management
- **rate_limiter.py** - OSINT rate limiting

#### 📊 Performance Tracking (`performance_modules/`)
- **performance_tracker.py** - Portfolio performance tracking
- **return_calculator.py** - Return calculations
- **risk_metrics.py** - Risk metric calculations
- **benchmark_comparison.py** - S&P 500 comparison

#### 🎯 Strategy Management (`strategy_modules/`)
- **portfolio_optimizer.py** - Portfolio optimization
- **weight_calculator.py** - Asset weight calculation
- **risk_calculator.py** - Risk assessment
- **data_validator.py** - Strategy validation

#### 🌍 Specialized Trackers
- **momentum_detector.py** - Momentum signal detection
- **regulatory_tracker.py** - Regulatory change tracking
- **agro_robotics_tracker.py** - Agriculture tech tracking
- **supply_chain_mapper.py** - Supply chain analysis
- **signal_integrator.py** - Signal integration

### API Routes (`routers/`)

| Router | Endpoints | Purpose |
|--------|-----------|---------|
| **extreme_signals.py** | `/extreme/*` | Extreme alpha detection (10 endpoints) |
| **investment.py** | `/investment/*` | Investment recommendations (6 endpoints) |
| **analysis.py** | `/analysis/*` | Technical/fundamental analysis (8 endpoints) |
| **signals.py** | `/signals/*` | Signal detection (14 endpoints) |
| **momentum.py** | `/momentum/*` | Momentum tracking (15 endpoints) |
| **integrated_signals.py** | `/integrated/*` | Cross-source signals (9 endpoints) |
| **auth.py** | `/auth/*` | Authentication (7 endpoints) |
| **portfolio_calculations.py** | `/portfolio/*` | Portfolio math (8 endpoints) |
| **strategy.py** | `/strategy/*` | Strategy management (6 endpoints) |
| **assets.py** | `/assets/*` | Asset management (7 endpoints) |
| **news.py** | `/news/*` | News data (5 endpoints) |
| **benchmark.py** | `/benchmark/*` | Benchmarking (4 endpoints) |
| **diagnostics.py** | `/diagnostics/*` | System diagnostics (6 endpoints) |
| **index.py** | `/index/*` | Index operations (5 endpoints) |
| **tasks.py** | `/tasks/*` | Background tasks (4 endpoints) |
| **manual_refresh.py** | `/manual/*` | Manual operations (3 endpoints) |
| **background.py** | `/background/*` | Background jobs (3 endpoints) |
| **health.py** | `/health/*` | Health checks (2 endpoints) |
| **metrics.py** | `/metrics/*` | System metrics (3 endpoints) |
| **system_status.py** | `/status/*` | System status (2 endpoints) |
| **root.py** | `/` | Root endpoints (2 endpoints) |

**Total API Endpoints: 150+**

## 🎨 Frontend Modules (`apps/web/app/`)

### Core Architecture (`core/`)

#### Domain Layer (`domain/`)
- **entities/** - Business entities (User, Portfolio, DataQuality, SystemHealth)
- **repositories/** - Repository interfaces
- **usecases/** - Business use cases

#### Application Layer (`application/`)
- **usecases/auth/** - Authentication use cases (Login, GoogleAuth)

#### Infrastructure Layer (`infrastructure/`)
- **api/** - API clients (HttpClient, ApiClient)
- **auth/** - Auth providers (GoogleAuth, TokenManager)
- **repositories/** - Repository implementations

#### Presentation Layer (`presentation/`)
- **components/** - UI components (ProtectedRoute, DataQuality, SystemHealth)
- **contexts/** - React contexts (AuthContext)
- **hooks/** - Custom hooks (useApiRequest, useDataQuality, useSystemHealth)

### Dashboard (`dashboard/`)
- **page.tsx** - Main dashboard page
- **extreme-signals/page.tsx** - Extreme signals dashboard
- **components/** - Dashboard components
  - DashboardMetrics.tsx
  - AllocationChart.tsx
  - PortfolioChart.tsx
  - SimulationPanel.tsx
- **hooks/** - Dashboard hooks
  - useDashboardData.ts
  - useChartControls.ts
  - useSimulation.ts

### Components (`components/`)

#### Strategy Configuration (`StrategyConfig/`)
- **StrategyForm.tsx** - Strategy form interface
- **BacktestResults.tsx** - Backtest display
- **RiskSettings.tsx** - Risk configuration
- **ValidationRules.tsx** - Validation logic
- **WeightAllocation.tsx** - Weight management

#### Performance Charts (`dashboard/PerformanceChart/`)
- **index.tsx** - Main chart component
- **ChartControlsPanel.tsx** - Chart controls
- **AssetSelector.tsx** - Asset selection
- **ChartTooltip.tsx** - Tooltip display
- **chartConfig.ts** - Chart configuration
- **chartDataProcessor.ts** - Data processing

#### Shared Components (`shared/`)
- **Button/** - Button component system
- **Card/** - Card component system
- **ErrorBoundary.tsx** - Error handling
- **LoadingSkeleton.tsx** - Loading states
- **TaskNotifications.tsx** - Notifications

### Services (`services/api/`)
- **client.ts** - Base API client
- **diagnostics.ts** - Diagnostics API
- **strategy.ts** - Strategy API
- **portfolio.ts** - Portfolio API
- **market.ts** - Market data API
- **news.ts** - News API
- **benchmark.ts** - Benchmark API
- **background.ts** - Background tasks API
- **manual.ts** - Manual operations API

### Pages
- **page.tsx** - Home page
- **login/page.tsx** - Login page
- **register/page.tsx** - Registration page
- **dashboard/page.tsx** - Dashboard
- **dashboard/extreme-signals/page.tsx** - Extreme signals
- **diagnostics/page.tsx** - System diagnostics
- **strategy/page.tsx** - Strategy configuration
- **news/page.tsx** - News feed
- **tasks/page.tsx** - Task management
- **admin/page.tsx** - Admin panel

## 🧪 Testing Infrastructure

### Backend Tests (`apps/api/tests/`)
- **unit/** - 321 unit tests
  - models/ - Model tests
  - routers/ - Route tests
  - services/ - Service tests
  - schemas/ - Schema tests
  - utils/ - Utility tests
- **integration/** - 8 integration tests
- **smoke/** - 12 production health checks
- **factories/** - Test data factories

### Frontend Tests (`apps/web/app/__tests__/`)
- **components/** - Component tests
- **hooks/** - Hook tests
- **services/** - Service tests
- **setup/** - Setup verification
- **utils/** - Test utilities

## 🔄 CI/CD Infrastructure (`.github/workflows/`)
- **ci-cd-pipeline.yml** - Main deployment pipeline
- **collect-signals.yml** - Signal collection workflow
- **dependency-review.yml** - Dependency security checks

## 📚 Documentation (`docs/`)

### Status Documentation (`00-project-status/`)
- Current status reports
- Test progress tracking
- Refactoring status
- Changelog

### Getting Started (`01-getting-started/`)
- Quick start guide
- Environment setup
- Dependency management

### API Reference (`02-api-reference/`)
- Complete API documentation
- Authentication guide
- Quick reference cards

### Implementation (`03-implementation/`)
- System architecture
- Clean architecture docs
- Testing strategy
- Operations guide

### Features (`04-features/`)
- Implemented features
- Planned features
- AI agent architecture

### Roadmap (`05-roadmap/`)
- Project roadmap
- Critical tasks
- High priority items

### Master Documents
- **MASTER_IMPLEMENTATION_PLAN.md** - Zero-budget architecture
- **SIGNAL_DETECTION_SYSTEM.md** - Signal detection documentation
- **PLATFORM_PHILOSOPHY.md** - Platform philosophy
- **INDEX.md** - Documentation index

## 📊 Module Statistics

| Category | Count |
|----------|-------|
| Backend Services | 45+ |
| API Routers | 22 |
| API Endpoints | 150+ |
| Database Models | 8 |
| Frontend Pages | 10 |
| Frontend Components | 30+ |
| Test Files | 50+ |
| Total Tests | 341 |
| Documentation Files | 76 |

## 🚀 Key Integration Points

### Data Flow
1. **Collection** → Collectors gather data from sources
2. **Processing** → Alpha detection analyzes patterns
3. **Storage** → Signals stored in PostgreSQL
4. **API** → FastAPI serves data
5. **Frontend** → Next.js displays signals
6. **Action** → Users receive recommendations

### Service Dependencies
- Signal Processor → Alpha Detection
- Investment Engine → Technical + Fundamental Analysis
- Meme Velocity → Multiple Collectors
- Extreme Backtest → Historical Data
- Dashboard → All API endpoints

This comprehensive module index provides a complete map of the Waardhaven AutoIndex codebase, enabling developers to quickly locate and understand any component of the system.