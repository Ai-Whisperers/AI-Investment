# Critical TODOs 🔴

[← Back to TODO](README.md)

## 0. URGENT: Comprehensive Testing Suite Implementation
**Impact**: Financial data integrity, regulatory compliance, production stability
**Coverage Target**: 95%+ (Financial industry standard)
**Effort**: 1-2 weeks

### Why This Is Now Priority #0
- **Financial Risk**: Untested portfolio calculations could cause significant financial losses
- **Regulatory**: Financial systems require auditable testing for compliance
- **Current Coverage**: ~25% is unacceptable for production financial systems
- **TDD Approach**: Write tests BEFORE fixing other critical issues

### Core Testing Requirements
```yaml
Coverage Requirements:
  - Portfolio Calculations: 100% (CRITICAL)
  - Risk Models: 100% (CRITICAL)
  - Performance Metrics: 100% (CRITICAL)
  - API Endpoints: 95%+
  - Frontend Components: 90%+
  - Integration: 95%+
```

### Implementation Plan
- [ ] Set up test infrastructure (pytest-cov, React Testing Library, Playwright)
- [ ] Write unit tests for ALL financial calculations
- [ ] Implement contract testing between frontend/backend
- [ ] Create E2E tests for critical user journeys
- [ ] Add performance tests (100k events/sec requirement)
- [ ] Configure CI/CD with coverage gates

### Test Categories
1. **Fast Tests** (< 1s each)
   - Unit tests for business logic
   - Component tests without API calls
   - Mocked external services

2. **Slow Tests** (> 1s each)
   - Integration tests with database
   - Real Celery task tests
   - E2E browser tests

### Blocking Issues Until Complete
- ❌ Cannot migrate calculations without tests
- ❌ Cannot deploy to production without 95% coverage
- ❌ Cannot guarantee data integrity without test suite

**See detailed specification**: [Testing Strategy](../../03-implementation/backend/testing/TESTING_STRATEGY.md)

---

## 1. Code Structure Refactoring (Pre-Testing Requirement)
**Impact**: Testing becomes impossible with god files, violates clean architecture
**Priority**: MUST complete before comprehensive testing
**Effort**: 3-4 days
**Status**: ⚠️ PARTIALLY COMPLETE (20% done - 4 of 20 files refactored)

### Frontend Structure Issues
- [x] ✅ **Dashboard God File** (797 → 173 lines): `apps/web/app/dashboard/page.tsx` - **COMPLETED**
  - Extracted: DashboardMetrics, PortfolioChart, AllocationChart, ChartControls, SimulationPanel
  - Created hooks: useDashboardData, useSimulation, useChartControls
  - Added DashboardProvider for context management

- [x] ✅ **PerformanceChart Component** (547 → 281 lines): **COMPLETED**
  - Extracted: ChartTooltip, ChartControlsPanel, AssetSelector
  - Created utilities: chartConfig, chartDataProcessor
  - Modularized into PerformanceChart/ directory structure

- [x] ✅ **Diagnostics Page** (524 → 90 lines): **COMPLETED**
  - Extracted: SystemSummaryCard, DatabaseStatusCard, CacheStatusCard, RefreshStatusCard
  - Created hook: useDiagnosticsData for state management

- [ ] **StrategyConfig Component** (488 lines): Multiple responsibilities
  - Split into smaller strategy components
  - Extract validation logic
  - Move calculations to domain layer

### Backend Structure Issues  
- [x] ✅ **Strategy Service** (633 → 284 lines): `app/services/strategy.py` - **COMPLETED**
  - Extracted: DataValidator, WeightCalculator, RiskCalculator, PortfolioOptimizer
  - Created modular strategy/ directory with single-responsibility modules

- [ ] **News Service** (564 lines): Too many responsibilities
  - Extract sentiment analysis
  - Separate entity extraction
  - Move aggregation logic

- [ ] **TwelveData Service** (535 lines): Mixed provider and service logic
  - Separate API client from business logic
  - Extract data transformation
  - Move caching logic to decorator

- [ ] **TwelveData Provider** (513 lines): Duplicate implementation
  - Consolidate with service refactoring

- [ ] **Performance Service** (498 lines): Mixed calculations
  - Extract return calculations
  - Separate risk metrics
  - Split benchmark comparison

- [ ] **Diagnostics Router** (444 lines): Too many endpoints
  - Split into health, metrics, and status routers
  - Extract diagnostic services
  - Separate concerns

- [ ] **Background Tasks** (370 lines): All task types in one file
  - Split into task-specific modules

- [ ] **MarketAux Provider** (357 lines): Mixed concerns
  - Extract API client from processing logic

### Clean Architecture Compliance
- [ ] Frontend: Complete migration to core/ clean architecture pattern
  - Move remaining business logic from components to use cases
  - Ensure all API calls go through repositories
  - Separate presentation from domain logic

- [ ] Backend: Implement proper layering
  - Create domain layer with business entities
  - Implement repository pattern for data access
  - Use dependency injection consistently
  - Separate infrastructure from business logic

### Benefits After Refactoring
- ✅ Each file under 250 lines (testable size)
- ✅ Single responsibility per module
- ✅ 95%+ test coverage becomes achievable
- ✅ Easier to maintain and extend
- ✅ Clear separation of concerns

---

## 2. Frontend Calculations Migration
**Impact**: Performance, scalability, data consistency
**Location**: `apps/web/app/lib/calculations/`
**Effort**: 2-3 days

### Tasks
- [ ] Identify all calculation functions in frontend
- [ ] Create corresponding backend endpoints
- [ ] Migrate calculation logic to Python
- [ ] Update frontend to use API calls
- [ ] Test calculation accuracy
- [ ] Remove frontend calculation code

### Affected Files
- `apps/web/app/lib/calculations/portfolio.ts`
- `apps/web/app/lib/calculations/performance.ts`
- `apps/web/app/lib/calculations/risk.ts`

---

## 3. CI/CD Pipeline Test Failures
**Impact**: Can't detect breaking changes
**Location**: `.github/workflows/`
**Effort**: 4-6 hours

### Tasks
- [ ] Remove `|| true` from test commands
- [ ] Fix failing backend tests
- [ ] Fix TypeScript compilation errors
- [ ] Add frontend test suite
- [ ] Configure test coverage reporting
- [ ] Set up test failure notifications

### Commands to Fix
```bash
# Current (broken)
npm test || true

# Should be
npm test
```

---

## 4. Database Migration System
**Impact**: Cannot safely update schema
**Effort**: 1-2 days

### Tasks
- [ ] Install and configure Alembic
- [ ] Create initial migration from current schema
- [ ] Document migration procedures
- [ ] Add migration to startup script
- [ ] Test rollback procedures
- [ ] Create migration for asset_news type fix

### Setup Commands
```bash
pip install alembic
alembic init migrations
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

---

## 5. Data Loss Prevention
**Impact**: Potential data loss on updates
**Location**: `apps/api/app/services/`
**Effort**: 1 day

### Tasks
- [ ] Audit all DELETE operations
- [ ] Replace with soft deletes
- [ ] Add transaction wrappers
- [ ] Implement backup before updates
- [ ] Add data recovery endpoints
- [ ] Test rollback scenarios

---

## 6. API Integration Optimization
**Impact**: Rate limits, incomplete data
**Effort**: 2 days

### TwelveData Issues
- [ ] Implement request batching
- [ ] Add caching layer
- [ ] Optimize API calls
- [ ] Handle rate limits gracefully
- [ ] Add fallback data sources

### MarketAux Integration
- [ ] Complete provider implementation
- [ ] Add sentiment analysis
- [ ] Implement entity extraction
- [ ] Create news aggregation pipeline
- [ ] Add to background tasks

---

## Acceptance Criteria
All critical issues must:
- Have 100% test coverage
- Include documentation
- Pass code review
- Be deployed to staging first
- Have rollback plan

---
[← Back to TODO](README.md) | [High Priority →](HIGH_PRIORITY.md)