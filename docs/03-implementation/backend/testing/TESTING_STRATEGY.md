---
title: Comprehensive Testing Strategy for Financial Systems
category: Testing
priority: 0
status: critical
last-updated: 2025-01-19
owner: qa-team
---

# 🧪 Comprehensive Testing Strategy

## Executive Summary

This document defines a **financial-grade testing strategy** with **95%+ coverage requirement** using Test-Driven Development (TDD) methodology. All financial calculations, risk models, and trading workflows MUST be tested before deployment.

## Coverage Requirements

```yaml
Minimum Coverage Targets:
  Overall: 95%
  Critical Systems:
    Portfolio Calculations: 100%
    Risk Models: 100%
    Performance Metrics: 100%
    Authentication: 100%
    Payment Processing: 100%
  Standard Systems:
    API Endpoints: 95%
    Business Logic: 95%
    Frontend Components: 90%
    Integration Tests: 95%
```

## Prerequisites: Code Structure Requirements

### ⚠️ CRITICAL: Refactoring Required Before Testing

Current god files and mixed responsibilities make comprehensive testing impossible. The following refactoring MUST be completed first:

#### Frontend Prerequisites
- **Dashboard page (797 lines)** → Split into 5+ components (max 150 lines each)
- **PerformanceChart (547 lines)** → Extract into 3+ modules
- **Diagnostics page (524 lines)** → Separate into health, metrics, status components
- **StrategyConfig (488 lines)** → Break into validation, UI, and logic modules

#### Backend Prerequisites  
- **Strategy service (633 lines)** → Split into validator, optimizer, risk modules
- **News service (564 lines)** → Separate sentiment, extraction, aggregation
- **TwelveData service (535 lines)** → Divide client, transformer, cache layers
- **Diagnostics router (444 lines)** → Split into health, metrics, status routers

#### Clean Architecture Compliance
- All business logic must be in domain/use case layers (not in UI components)
- API calls must go through repository interfaces
- Services must follow single responsibility principle
- Dependencies must be injected, not hardcoded

**See [CRITICAL TODOs](../../../05-roadmap/CRITICAL.md#1-code-structure-refactoring-pre-testing-requirement) for detailed refactoring plan**

## Testing Architecture

```mermaid
graph TB
    subgraph "Test Pyramid"
        Unit[Unit Tests<br/>70% - Fast, Isolated]
        Integration[Integration Tests<br/>20% - API, Database]
        E2E[E2E Tests<br/>10% - User Workflows]
    end
    
    subgraph "Test Types"
        Contract[Contract Tests<br/>Frontend ↔ Backend]
        Performance[Performance Tests<br/>100k events/sec]
        Security[Security Tests<br/>Penetration, OWASP]
        Visual[Visual Regression<br/>UI Screenshots]
    end
    
    Unit --> Integration
    Integration --> E2E
    E2E --> Contract
    Contract --> Performance
    Performance --> Security
    Security --> Visual
```

## 1. Backend Testing (FastAPI + Python)

### 1.1 Unit Tests - Portfolio Calculations

```python
# tests/unit/test_portfolio_calculations.py
import pytest
from decimal import Decimal
from app.services.portfolio import PortfolioCalculator

class TestPortfolioCalculations:
    """Critical: 100% coverage required for financial calculations"""
    
    @pytest.fixture
    def calculator(self):
        return PortfolioCalculator()
    
    def test_portfolio_value_calculation(self, calculator):
        """Test portfolio value with multiple assets"""
        positions = [
            {"symbol": "AAPL", "shares": 100, "price": Decimal("150.00")},
            {"symbol": "GOOGL", "shares": 50, "price": Decimal("2800.00")}
        ]
        expected = Decimal("155000.00")  # (100*150) + (50*2800)
        assert calculator.calculate_total_value(positions) == expected
    
    def test_weighted_returns(self, calculator):
        """Test time-weighted return calculation"""
        cash_flows = [
            {"date": "2024-01-01", "amount": Decimal("10000")},
            {"date": "2024-06-01", "amount": Decimal("5000")}
        ]
        ending_value = Decimal("16500")
        expected_return = Decimal("0.10")  # 10% return
        assert calculator.calculate_twr(cash_flows, ending_value) == expected_return
    
    @pytest.mark.parametrize("volatility,return_rate,expected_sharpe", [
        (Decimal("0.15"), Decimal("0.12"), Decimal("0.80")),
        (Decimal("0.20"), Decimal("0.15"), Decimal("0.75")),
        (Decimal("0.10"), Decimal("0.08"), Decimal("0.80"))
    ])
    def test_sharpe_ratio_calculation(self, calculator, volatility, return_rate, expected_sharpe):
        """Parameterized test for Sharpe ratio calculations"""
        risk_free_rate = Decimal("0.02")
        result = calculator.calculate_sharpe_ratio(return_rate, risk_free_rate, volatility)
        assert abs(result - expected_sharpe) < Decimal("0.01")
```

### 1.2 Risk Model Tests

```python
# tests/unit/test_risk_models.py
import pytest
import numpy as np
from app.services.risk import RiskAnalyzer

class TestRiskModels:
    """Critical: Risk calculations must be 100% accurate"""
    
    def test_value_at_risk_calculation(self):
        """Test VaR calculation at 95% confidence"""
        returns = np.array([-0.02, 0.01, -0.015, 0.03, -0.01, 0.02, -0.005])
        risk_analyzer = RiskAnalyzer()
        var_95 = risk_analyzer.calculate_var(returns, confidence=0.95)
        assert var_95 == pytest.approx(-0.0175, rel=1e-4)
    
    def test_maximum_drawdown(self):
        """Test maximum drawdown calculation"""
        prices = [100, 110, 105, 115, 95, 100, 90, 95]
        risk_analyzer = RiskAnalyzer()
        max_dd = risk_analyzer.calculate_max_drawdown(prices)
        assert max_dd == pytest.approx(-0.2174, rel=1e-4)  # -21.74%
    
    def test_beta_calculation(self):
        """Test beta calculation against market"""
        portfolio_returns = np.array([0.02, 0.01, -0.01, 0.03, 0.015])
        market_returns = np.array([0.015, 0.008, -0.005, 0.025, 0.01])
        risk_analyzer = RiskAnalyzer()
        beta = risk_analyzer.calculate_beta(portfolio_returns, market_returns)
        assert beta == pytest.approx(1.15, rel=1e-2)
```

### 1.3 API Contract Tests

```python
# tests/contract/test_api_contracts.py
import pytest
from pydantic import ValidationError
from app.schemas.portfolio import PortfolioResponse
from app.schemas.index import IndexValueRequest

class TestAPIContracts:
    """Ensure frontend-backend contract compatibility"""
    
    def test_portfolio_response_contract(self):
        """Test portfolio response matches frontend expectations"""
        response_data = {
            "total_value": 100000.00,
            "positions": [
                {"symbol": "AAPL", "shares": 100, "value": 15000.00}
            ],
            "performance": {
                "daily_return": 0.0125,
                "total_return": 0.0850
            }
        }
        # This should not raise ValidationError
        validated = PortfolioResponse(**response_data)
        assert validated.total_value == 100000.00
    
    def test_index_calculation_request_contract(self):
        """Test index calculation request validation"""
        invalid_request = {
            "start_date": "invalid-date",
            "end_date": "2024-01-01"
        }
        with pytest.raises(ValidationError) as exc_info:
            IndexValueRequest(**invalid_request)
        assert "date" in str(exc_info.value).lower()
```

### 1.4 Provider Tests with Mocking

```python
# tests/unit/test_providers.py
import pytest
from unittest.mock import patch, Mock
from app.providers.twelvedata_provider import TwelveDataProvider

class TestTwelveDataProvider:
    """Test external API providers with realistic mocks"""
    
    @pytest.fixture
    def provider(self):
        return TwelveDataProvider(api_key="test_key")
    
    @patch('requests.get')
    def test_fetch_price_data(self, mock_get, provider):
        """Test price fetching with realistic TwelveData response"""
        # Mock realistic TwelveData response pattern
        mock_response = Mock()
        mock_response.json.return_value = {
            "meta": {
                "symbol": "AAPL",
                "interval": "1day",
                "currency": "USD",
                "exchange": "NASDAQ"
            },
            "values": [
                {
                    "datetime": "2024-01-19",
                    "open": "149.50",
                    "high": "151.00",
                    "low": "149.00",
                    "close": "150.25",
                    "volume": "58245100"
                }
            ],
            "status": "ok"
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = provider.fetch_price("AAPL", "2024-01-19")
        assert result["close"] == 150.25
        assert result["volume"] == 58245100
    
    @patch('requests.get')
    def test_handle_rate_limit(self, mock_get, provider):
        """Test rate limit handling"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            "code": 429,
            "message": "You have exceeded the API rate limit"
        }
        mock_get.return_value = mock_response
        
        with pytest.raises(RateLimitException):
            provider.fetch_price("AAPL", "2024-01-19")
```

### 1.5 Integration Tests with Test Database

```python
# tests/integration/test_portfolio_integration.py
import pytest
from sqlalchemy import create_engine
from app.models import Portfolio, Asset, Price
from app.services.portfolio_service import PortfolioService

@pytest.fixture(scope="session")
def test_db():
    """Create test database for integration tests"""
    engine = create_engine("postgresql://test:test@localhost/test_waardhaven")
    # Setup test data
    yield engine
    # Cleanup

class TestPortfolioIntegration:
    """Integration tests with real database"""
    
    @pytest.mark.slow
    def test_portfolio_creation_workflow(self, test_db):
        """Test complete portfolio creation workflow"""
        service = PortfolioService(db=test_db)
        
        # Create portfolio
        portfolio = service.create_portfolio(
            user_id=1,
            name="Test Portfolio",
            initial_value=100000
        )
        
        # Add positions
        positions = [
            {"symbol": "AAPL", "shares": 100},
            {"symbol": "GOOGL", "shares": 50}
        ]
        service.add_positions(portfolio.id, positions)
        
        # Calculate value
        total_value = service.calculate_portfolio_value(portfolio.id)
        assert total_value > 0
        
        # Verify in database
        stored_portfolio = test_db.query(Portfolio).filter_by(id=portfolio.id).first()
        assert stored_portfolio.name == "Test Portfolio"
```

### 1.6 Celery Task Tests

```python
# tests/integration/test_celery_tasks.py
import pytest
from celery import Celery
from app.tasks import refresh_market_data, calculate_portfolio_metrics

@pytest.fixture
def celery_app():
    """Configure Celery for testing"""
    app = Celery('test')
    app.conf.update(
        task_always_eager=True,  # Execute tasks synchronously for testing
        task_eager_propagates=True
    )
    return app

class TestCeleryTasks:
    """Test background tasks"""
    
    @pytest.mark.slow
    def test_market_data_refresh_task(self, celery_app, test_db):
        """Test market data refresh task"""
        result = refresh_market_data.apply(args=['AAPL', 'GOOGL'])
        assert result.successful()
        assert result.result['status'] == 'success'
    
    @pytest.mark.fast
    def test_portfolio_metrics_calculation(self, celery_app):
        """Test portfolio metrics calculation task"""
        portfolio_data = {
            "positions": [
                {"symbol": "AAPL", "shares": 100, "price": 150}
            ]
        }
        result = calculate_portfolio_metrics.apply(kwargs=portfolio_data)
        assert 'sharpe_ratio' in result.result
        assert 'max_drawdown' in result.result
```

## 2. Frontend Testing (Next.js + React)

### 2.1 Component Tests with React Testing Library

```typescript
// tests/components/PortfolioAllocation.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PortfolioAllocation } from '@/components/PortfolioAllocation';
import { server } from '@/mocks/server';
import { rest } from 'msw';

describe('PortfolioAllocation Component', () => {
  it('displays portfolio allocations correctly', async () => {
    const mockData = {
      allocations: [
        { symbol: 'AAPL', weight: 0.30, value: 30000 },
        { symbol: 'GOOGL', weight: 0.25, value: 25000 }
      ]
    };
    
    render(<PortfolioAllocation portfolioId="123" />);
    
    await waitFor(() => {
      expect(screen.getByText('AAPL - 30%')).toBeInTheDocument();
      expect(screen.getByText('GOOGL - 25%')).toBeInTheDocument();
    });
  });
  
  it('handles rebalancing action', async () => {
    const user = userEvent.setup();
    render(<PortfolioAllocation portfolioId="123" />);
    
    const rebalanceButton = await screen.findByRole('button', { name: /rebalance/i });
    await user.click(rebalanceButton);
    
    await waitFor(() => {
      expect(screen.getByText(/rebalancing complete/i)).toBeInTheDocument();
    });
  });
});
```

### 2.2 MSW (Mock Service Worker) Setup

```typescript
// mocks/handlers.ts
import { rest } from 'msw';

export const handlers = [
  // Mock portfolio endpoint
  rest.get('/api/v1/portfolio/:id', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        id: req.params.id,
        total_value: 100000,
        positions: [
          { symbol: 'AAPL', shares: 100, value: 15000 },
          { symbol: 'GOOGL', shares: 50, value: 140000 }
        ]
      })
    );
  }),
  
  // Mock price data endpoint with realistic TwelveData pattern
  rest.get('/api/v1/market/price/:symbol', (req, res, ctx) => {
    const prices = {
      'AAPL': { price: 150.25, change: 0.0125 },
      'GOOGL': { price: 2800.50, change: -0.0075 }
    };
    
    return res(
      ctx.status(200),
      ctx.json(prices[req.params.symbol as string] || { price: 100, change: 0 })
    );
  })
];
```

### 2.3 Visual Regression Tests

```typescript
// tests/visual/dashboard.visual.test.ts
import { test, expect } from '@playwright/test';

test.describe('Dashboard Visual Regression', () => {
  test('portfolio dashboard matches snapshot', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForSelector('[data-testid="portfolio-chart"]');
    
    // Take screenshot for comparison
    await expect(page).toHaveScreenshot('dashboard-full.png', {
      fullPage: true,
      threshold: 0.2  // Allow 20% difference for dynamic data
    });
  });
  
  test('dark mode visual consistency', async ({ page }) => {
    await page.goto('/dashboard');
    await page.click('[data-testid="theme-toggle"]');
    
    await expect(page).toHaveScreenshot('dashboard-dark-mode.png', {
      fullPage: true,
      threshold: 0.2
    });
  });
});
```

## 3. E2E Tests (Playwright)

### 3.1 Critical User Journey Tests

```typescript
// e2e/trading-workflow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Trading Workflow E2E', () => {
  test('complete portfolio creation and trading flow', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'TestPass123!');
    await page.click('[type="submit"]');
    
    // Navigate to portfolio creation
    await page.waitForURL('/dashboard');
    await page.click('[data-testid="create-portfolio"]');
    
    // Create portfolio
    await page.fill('[name="portfolio-name"]', 'Test Portfolio');
    await page.fill('[name="initial-value"]', '100000');
    await page.selectOption('[name="strategy"]', 'moderate');
    await page.click('[data-testid="submit-portfolio"]');
    
    // Verify portfolio created
    await expect(page.locator('h1')).toContainText('Test Portfolio');
    await expect(page.locator('[data-testid="portfolio-value"]')).toContainText('$100,000');
    
    // Add position
    await page.click('[data-testid="add-position"]');
    await page.fill('[name="symbol"]', 'AAPL');
    await page.fill('[name="shares"]', '100');
    await page.click('[data-testid="confirm-trade"]');
    
    // Verify position added
    await expect(page.locator('[data-testid="positions-table"]')).toContainText('AAPL');
  });
  
  test('risk analysis workflow', async ({ page }) => {
    await page.goto('/dashboard/risk-analysis');
    
    // Verify risk metrics displayed
    await expect(page.locator('[data-testid="sharpe-ratio"]')).toBeVisible();
    await expect(page.locator('[data-testid="max-drawdown"]')).toBeVisible();
    await expect(page.locator('[data-testid="var-95"]')).toBeVisible();
    
    // Test risk adjustment
    await page.click('[data-testid="adjust-risk"]');
    await page.selectOption('[name="risk-level"]', 'conservative');
    await page.click('[data-testid="apply-risk-settings"]');
    
    // Verify update
    await expect(page.locator('[data-testid="risk-level-indicator"]')).toContainText('Conservative');
  });
});
```

## 4. Performance Testing

### 4.1 Load Testing with Locust

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between
import json

class FinancialSystemUser(HttpUser):
    """Simulate 100k events/sec requirement"""
    wait_time = between(0.1, 0.5)
    
    def on_start(self):
        """Login before testing"""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "loadtest@example.com",
            "password": "LoadTest123!"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def get_portfolio_value(self):
        """High frequency operation - portfolio value check"""
        self.client.get("/api/v1/portfolio/current", headers=self.headers)
    
    @task(2)
    def get_market_prices(self):
        """Market data fetching"""
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN"]
        for symbol in symbols:
            self.client.get(f"/api/v1/market/price/{symbol}", headers=self.headers)
    
    @task(1)
    def calculate_metrics(self):
        """Heavy calculation endpoint"""
        self.client.post("/api/v1/portfolio/calculate-metrics", 
                         json={"portfolio_id": "123"},
                         headers=self.headers)

# Run with: locust -f locustfile.py --host=http://localhost:8000 --users=1000 --spawn-rate=100
```

### 4.2 Performance Benchmarks

```python
# tests/performance/test_benchmarks.py
import pytest
import time
from app.services.portfolio import PortfolioCalculator

class TestPerformanceBenchmarks:
    """Ensure calculations meet performance requirements"""
    
    @pytest.mark.benchmark
    def test_portfolio_calculation_performance(self, benchmark):
        """Portfolio calculation must complete in <10ms"""
        calculator = PortfolioCalculator()
        positions = [{"symbol": f"STOCK{i}", "shares": 100, "price": 150.0} 
                    for i in range(100)]  # 100 positions
        
        result = benchmark(calculator.calculate_total_value, positions)
        assert benchmark.stats['mean'] < 0.010  # 10ms
    
    @pytest.mark.benchmark
    def test_risk_calculation_performance(self, benchmark):
        """Risk metrics must calculate in <50ms for 1000 data points"""
        import numpy as np
        from app.services.risk import RiskAnalyzer
        
        analyzer = RiskAnalyzer()
        returns = np.random.normal(0.001, 0.02, 1000)  # 1000 daily returns
        
        def calculate_all_metrics():
            return {
                'var': analyzer.calculate_var(returns),
                'sharpe': analyzer.calculate_sharpe_ratio(returns),
                'max_dd': analyzer.calculate_max_drawdown(returns)
            }
        
        result = benchmark(calculate_all_metrics)
        assert benchmark.stats['mean'] < 0.050  # 50ms
```

## 5. Test Infrastructure

### 5.1 pytest Configuration

```ini
# pytest.ini
[tool:pytest]
minversion = 7.0
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Markers for test categorization
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests with database
    slow: Tests that take >1s
    fast: Tests that take <1s
    benchmark: Performance benchmark tests
    contract: API contract tests
    critical: Must pass for deployment

# Coverage settings
addopts = 
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=95
    --strict-markers
    -v

# Test execution profiles
[tool:pytest:fast]
addopts = -m "fast and not slow"

[tool:pytest:ci]
addopts = -m "not benchmark" --maxfail=1
```

### 5.2 CI/CD Pipeline Configuration

```yaml
# .github/workflows/test.yml
name: Comprehensive Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  fast-tests:
    name: Fast Tests (Unit + Contracts)
    runs-on: ubuntu-latest
    timeout-minutes: 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements-test.txt
      
      - name: Run fast tests
        run: |
          pytest -m "fast" --cov-fail-under=95
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          fail_ci_if_error: true

  slow-tests:
    name: Slow Tests (Integration + E2E)
    runs-on: ubuntu-latest
    timeout-minutes: 30
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Run integration tests
        run: |
          pytest -m "slow" --cov-fail-under=95
      
      - name: Run E2E tests
        run: |
          npx playwright test

  performance-tests:
    name: Performance Benchmarks
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
      - name: Run performance tests
        run: |
          pytest -m "benchmark" --benchmark-only
          locust -f tests/performance/locustfile.py --headless -u 100 -r 10 -t 60s

  deploy-gate:
    name: Deployment Gate Check
    needs: [fast-tests, slow-tests]
    runs-on: ubuntu-latest
    
    steps:
      - name: Check coverage threshold
        run: |
          if [ $(coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//') -lt 95 ]; then
            echo "Coverage below 95% threshold. Deployment blocked."
            exit 1
          fi
```

### 5.3 Test Data Factory

```python
# tests/factories.py
import factory
from factory import fuzzy
from decimal import Decimal
from datetime import datetime, timedelta
from app.models import User, Portfolio, Asset, Price

class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Generate test users"""
    class Meta:
        model = User
    
    email = factory.Faker('email')
    username = factory.Faker('user_name')
    is_active = True

class AssetFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Generate test assets"""
    class Meta:
        model = Asset
    
    symbol = factory.Sequence(lambda n: f"TEST{n}")
    name = factory.Faker('company')
    asset_type = fuzzy.FuzzyChoice(['stock', 'etf', 'commodity'])
    
class PriceFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Generate realistic price data"""
    class Meta:
        model = Price
    
    asset = factory.SubFactory(AssetFactory)
    date = fuzzy.FuzzyDate(datetime.now() - timedelta(days=365))
    open = fuzzy.FuzzyDecimal(50, 500, precision=2)
    close = factory.LazyAttribute(lambda obj: obj.open * Decimal(random.uniform(0.95, 1.05)))
    high = factory.LazyAttribute(lambda obj: max(obj.open, obj.close) * Decimal(1.02))
    low = factory.LazyAttribute(lambda obj: min(obj.open, obj.close) * Decimal(0.98))
    volume = fuzzy.FuzzyInteger(1000000, 100000000)

class PortfolioFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Generate test portfolios"""
    class Meta:
        model = Portfolio
    
    user = factory.SubFactory(UserFactory)
    name = factory.Faker('catch_phrase')
    initial_value = fuzzy.FuzzyDecimal(10000, 1000000, precision=2)
    
    @factory.post_generation
    def positions(self, create, extracted, **kwargs):
        """Add positions after portfolio creation"""
        if not create:
            return
        
        if extracted:
            for position in extracted:
                self.positions.append(position)
```

## 6. Testing Best Practices

### 6.1 TDD Workflow

```python
"""
TDD Cycle for Financial Calculations:
1. RED: Write failing test first
2. GREEN: Write minimal code to pass
3. REFACTOR: Improve code quality
"""

# Step 1: Write test first (RED)
def test_calculate_portfolio_beta():
    """Beta calculation against market benchmark"""
    portfolio_returns = [0.02, 0.01, -0.01, 0.03]
    market_returns = [0.015, 0.008, -0.005, 0.025]
    
    calculator = PortfolioCalculator()
    beta = calculator.calculate_beta(portfolio_returns, market_returns)
    
    assert beta == pytest.approx(1.15, rel=0.01)

# Step 2: Implement minimal code (GREEN)
def calculate_beta(self, portfolio_returns, market_returns):
    covariance = np.cov(portfolio_returns, market_returns)[0][1]
    market_variance = np.var(market_returns)
    return covariance / market_variance

# Step 3: Refactor for production (REFACTOR)
def calculate_beta(
    self, 
    portfolio_returns: np.ndarray, 
    market_returns: np.ndarray,
    min_periods: int = 20
) -> Decimal:
    """
    Calculate portfolio beta against market benchmark.
    
    Args:
        portfolio_returns: Array of portfolio returns
        market_returns: Array of market returns
        min_periods: Minimum periods for valid calculation
    
    Returns:
        Beta coefficient as Decimal
    
    Raises:
        InsufficientDataError: If less than min_periods
        CalculationError: If variance is zero
    """
    if len(portfolio_returns) < min_periods:
        raise InsufficientDataError(f"Need at least {min_periods} periods")
    
    covariance = np.cov(portfolio_returns, market_returns)[0][1]
    market_variance = np.var(market_returns)
    
    if market_variance == 0:
        raise CalculationError("Market variance is zero")
    
    return Decimal(str(covariance / market_variance)).quantize(Decimal('0.0001'))
```

### 6.2 Critical Path Testing

```yaml
# Critical paths that MUST have 100% coverage
Critical Trading Paths:
  1. Portfolio Creation:
     - User authentication
     - Portfolio initialization
     - Initial deposit
     - Strategy selection
     
  2. Order Execution:
     - Order validation
     - Balance check
     - Price calculation
     - Position update
     - Transaction logging
     
  3. Risk Assessment:
     - Position limits
     - Margin requirements
     - Stop-loss triggers
     - Exposure calculation
     
  4. Performance Reporting:
     - Return calculation
     - Benchmark comparison
     - Fee deduction
     - Tax calculation
```

## 7. Smoke Tests for Production

```python
# tests/smoke/test_production_health.py
import pytest
import requests
from datetime import datetime

class TestProductionSmoke:
    """Quick tests to verify production deployment"""
    
    @pytest.fixture
    def api_url(self):
        return "https://waardhaven-api.onrender.com"
    
    def test_api_health(self, api_url):
        """API responds to health check"""
        response = requests.get(f"{api_url}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_critical_endpoints(self, api_url):
        """Critical endpoints are accessible"""
        endpoints = [
            "/api/v1/auth/login",
            "/api/v1/portfolio/current",
            "/api/v1/market/price/AAPL"
        ]
        
        for endpoint in endpoints:
            response = requests.options(f"{api_url}{endpoint}")
            assert response.status_code in [200, 204]
    
    def test_database_connectivity(self, api_url):
        """Database is connected and responding"""
        response = requests.get(f"{api_url}/api/v1/diagnostics/database-status")
        assert response.json()["status"] == "connected"
    
    def test_market_data_freshness(self, api_url):
        """Market data is recent (within 24 hours)"""
        response = requests.get(f"{api_url}/api/v1/diagnostics/data-freshness")
        last_update = datetime.fromisoformat(response.json()["last_update"])
        age_hours = (datetime.now() - last_update).total_seconds() / 3600
        assert age_hours < 24, f"Data is {age_hours} hours old"
```

## Summary

This comprehensive testing strategy ensures:
- **95%+ coverage** across all systems
- **100% coverage** for financial calculations
- **TDD methodology** for new features
- **Contract testing** for API compatibility
- **Performance testing** for 100k events/sec
- **E2E testing** for critical workflows
- **Automated CI/CD** with coverage gates

All tests are categorized (fast/slow) for efficient execution and clear failure identification in this high-stakes financial system.