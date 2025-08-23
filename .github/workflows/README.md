# CI/CD Pipeline Architecture

## ️ Clean Modular Design

This CI/CD architecture follows clean principles with separation of concerns, making it portable across platforms (GitHub Actions → Azure DevOps → GitLab CI).

##  Workflow Structure

```
.github/workflows/
├── test-backend.yml      # Backend testing & quality checks
├── test-frontend.yml     # Frontend testing & quality checks  
├── quality-gates.yml     # Unified quality gate enforcement
├── build-deploy.yml      # Build & deployment pipeline
├── security.yml          # Security scanning (existing)
└── deploy.yml           # Manual deployment (existing)
```

##  Pipeline Flow

### 1. **Test Workflows** (Parallel Execution)
- **Backend Tests** (`test-backend.yml`)
  - Fast unit tests (< 5 min)
  - Integration tests with PostgreSQL + Redis
  - Financial calculation tests (100% coverage)
  - Code quality (ruff, black, mypy)
  - Security scanning (safety, bandit)

- **Frontend Tests** (`test-frontend.yml`)
  - Jest unit tests with coverage
  - TypeScript compilation checks
  - ESLint & Prettier validation
  - Next.js build verification
  - Dependency security audit

### 2. **Quality Gates** (`quality-gates.yml`)
- Orchestrates both test workflows
- Enforces coverage thresholds
- Blocks deployment on failures
- Provides unified pass/fail status

### 3. **Build & Deploy** (`build-deploy.yml`)
- Requires quality gates to pass
- Builds multi-platform Docker images
- Auto-deploys to staging (main branch)
- Manual promotion to production
- Automated rollback on failure

##  Quality Standards

### Backend Requirements
- **Unit Tests**: 50%+ coverage (expandable)
- **Financial Tests**: 95%+ coverage (strict)
- **Integration Tests**: All critical paths
- **Code Quality**: Passes ruff, black, mypy
- **Security**: No high/critical vulnerabilities

### Frontend Requirements  
- **Unit Tests**: 50%+ coverage (expandable)
- **Type Safety**: TypeScript compilation success
- **Code Quality**: ESLint + Prettier compliance
- **Build**: Production build success
- **Security**: Dependency audit clean

##  Platform Portability

### GitHub Actions → Azure DevOps
```yaml
# GitHub Actions
- name: Run tests
  run: pytest tests/ -v

# Azure DevOps equivalent
- task: PythonScript@0
  displayName: 'Run tests'
  inputs:
    scriptSource: 'inline'
    script: 'pytest tests/ -v'
```

### GitHub Actions → GitLab CI
```yaml
# GitHub Actions
env:
  PYTHON_VERSION: '3.11'

# GitLab CI equivalent
variables:
  PYTHON_VERSION: '3.11'
```

##  Environment Configuration

### Required Secrets
```
CODECOV_TOKEN          # Coverage reporting
GITHUB_TOKEN          # Container registry access
SLACK_WEBHOOK         # Deployment notifications
```

### Required Variables
```
NEXT_PUBLIC_API_URL   # Frontend API endpoint
DATABASE_URL          # PostgreSQL connection
REDIS_URL            # Redis connection
JWT_SECRET_KEY       # Authentication secret
```

##  Local Testing

### Backend
```bash
cd apps/api
python -m pytest tests/unit -v --maxfail=5
python -m pytest -m "financial" --cov-fail-under=95
```

### Frontend
```bash
cd apps/web
npm test -- --ci --coverage --maxWorkers=2
npm run build
```

##  Health Checks

### Pipeline Health Indicators
-  **Green**: All tests passing, ready for deployment
- ️ **Yellow**: Non-critical failures, manual review needed
-  **Red**: Critical failures, deployment blocked

### Monitoring Dashboards
- **Test Results**: GitHub Actions summary
- **Coverage Trends**: Codecov.io dashboard  
- **Security Reports**: GitHub Security tab
- **Deployment Status**: Environment status pages

##  Migration Path

To migrate to other platforms:

1. **Extract Environment Variables**: All configs externalized
2. **Copy Job Logic**: Each job is self-contained
3. **Adapt Syntax**: Update platform-specific syntax only
4. **Test Incrementally**: Migrate one workflow at a time

##  Continuous Improvement

### Metrics to Track
- Test execution time (target: < 10 min total)
- Coverage trends (target: increasing over time)
- Security issue resolution time
- Deployment frequency and success rate

### Regular Reviews
- Monthly pipeline performance review
- Quarterly security tool updates
- Semi-annual architecture assessment