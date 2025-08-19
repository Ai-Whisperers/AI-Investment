# Critical TODOs 🔴

[← Back to TODO](README.md)

## 1. Frontend Calculations Migration
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

## 2. CI/CD Pipeline Test Failures
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

## 3. Database Migration System
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

## 4. Data Loss Prevention
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

## 5. API Integration Optimization
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