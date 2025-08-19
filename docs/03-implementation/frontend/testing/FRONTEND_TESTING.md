---
title: Frontend Testing Specification
category: Testing
priority: 1
status: critical
last-updated: 2025-01-19
owner: frontend-team
---

# 🎨 Frontend Testing Specification

## Overview

Comprehensive testing strategy for Next.js/React frontend with **90%+ coverage** requirement, focusing on financial UI accuracy, user workflows, and visual consistency.

## Testing Stack

```yaml
Testing Framework:
  Unit/Component: React Testing Library
  E2E: Playwright
  Visual Regression: Percy/Chromatic
  Mocking: MSW (Mock Service Worker)
  Coverage: Jest Coverage + NYC
  
Requirements:
  Component Coverage: 90%+
  E2E Coverage: Critical paths 100%
  Visual Regression: All pages
  Performance: <3s page load
```

## 1. Component Testing Strategy

### 1.1 Portfolio Components

```typescript
// tests/components/portfolio/PortfolioValue.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { PortfolioValue } from '@/components/portfolio/PortfolioValue';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { server } from '@/mocks/server';
import { rest } from 'msw';

describe('PortfolioValue Component', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );

  beforeEach(() => {
    queryClient.clear();
  });

  test('displays portfolio value with correct formatting', async () => {
    server.use(
      rest.get('/api/v1/portfolio/current', (req, res, ctx) => {
        return res(
          ctx.json({
            total_value: 125750.50,
            daily_change: 1250.25,
            daily_change_percent: 0.0101,
          })
        );
      })
    );

    render(<PortfolioValue portfolioId="123" />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('$125,750.50')).toBeInTheDocument();
      expect(screen.getByText('+$1,250.25')).toBeInTheDocument();
      expect(screen.getByText('+1.01%')).toBeInTheDocument();
    });

    // Verify color coding for gains
    const changeElement = screen.getByText('+1.01%');
    expect(changeElement).toHaveClass('text-green-600');
  });

  test('handles loading state correctly', () => {
    render(<PortfolioValue portfolioId="123" />, { wrapper });
    expect(screen.getByTestId('portfolio-value-skeleton')).toBeInTheDocument();
  });

  test('handles error state gracefully', async () => {
    server.use(
      rest.get('/api/v1/portfolio/current', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ error: 'Server error' }));
      })
    );

    render(<PortfolioValue portfolioId="123" />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/Unable to load portfolio/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    });
  });

  test('updates in real-time when data changes', async () => {
    const { rerender } = render(<PortfolioValue portfolioId="123" />, { wrapper });

    // Initial value
    await waitFor(() => {
      expect(screen.getByText('$125,750.50')).toBeInTheDocument();
    });

    // Simulate data update
    server.use(
      rest.get('/api/v1/portfolio/current', (req, res, ctx) => {
        return res(
          ctx.json({
            total_value: 126000.00,
            daily_change: 1500.00,
            daily_change_percent: 0.0120,
          })
        );
      })
    );

    // Trigger re-fetch
    queryClient.invalidateQueries(['portfolio', '123']);

    await waitFor(() => {
      expect(screen.getByText('$126,000.00')).toBeInTheDocument();
    });
  });
});
```

### 1.2 Risk Metrics Display

```typescript
// tests/components/risk/RiskMetrics.test.tsx
import { render, screen } from '@testing-library/react';
import { RiskMetrics } from '@/components/risk/RiskMetrics';

describe('RiskMetrics Component', () => {
  const mockMetrics = {
    sharpe_ratio: 1.45,
    sortino_ratio: 1.82,
    max_drawdown: -0.1523,
    var_95: -0.0234,
    beta: 1.12,
    volatility: 0.1823,
  };

  test('displays all risk metrics with correct formatting', () => {
    render(<RiskMetrics metrics={mockMetrics} />);

    // Sharpe Ratio
    expect(screen.getByText('Sharpe Ratio')).toBeInTheDocument();
    expect(screen.getByText('1.45')).toBeInTheDocument();

    // Max Drawdown (should show as positive percentage)
    expect(screen.getByText('Max Drawdown')).toBeInTheDocument();
    expect(screen.getByText('15.23%')).toBeInTheDocument();

    // VaR
    expect(screen.getByText('VaR (95%)')).toBeInTheDocument();
    expect(screen.getByText('2.34%')).toBeInTheDocument();

    // Beta
    expect(screen.getByText('Beta')).toBeInTheDocument();
    expect(screen.getByText('1.12')).toBeInTheDocument();
  });

  test('applies color coding based on risk levels', () => {
    render(<RiskMetrics metrics={mockMetrics} />);

    const sharpeElement = screen.getByTestId('sharpe-ratio-value');
    expect(sharpeElement).toHaveClass('text-green-600'); // Good Sharpe > 1

    const drawdownElement = screen.getByTestId('max-drawdown-value');
    expect(drawdownElement).toHaveClass('text-yellow-600'); // Moderate drawdown
  });

  test('shows tooltips with explanations', async () => {
    const { user } = render(<RiskMetrics metrics={mockMetrics} />);

    const sharpeInfo = screen.getByTestId('sharpe-ratio-info');
    await user.hover(sharpeInfo);

    await waitFor(() => {
      expect(screen.getByRole('tooltip')).toHaveTextContent(
        /Risk-adjusted return measure/i
      );
    });
  });
});
```

### 1.3 Trading Form Validation

```typescript
// tests/components/trading/TradeForm.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TradeForm } from '@/components/trading/TradeForm';

describe('TradeForm Component', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  test('validates required fields', async () => {
    const user = userEvent.setup();
    render(<TradeForm onSubmit={mockOnSubmit} />);

    // Try to submit without filling fields
    const submitButton = screen.getByRole('button', { name: /place order/i });
    await user.click(submitButton);

    // Check validation messages
    expect(screen.getByText(/Symbol is required/i)).toBeInTheDocument();
    expect(screen.getByText(/Quantity must be greater than 0/i)).toBeInTheDocument();
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  test('validates quantity limits', async () => {
    const user = userEvent.setup();
    render(<TradeForm onSubmit={mockOnSubmit} maxShares={100} />);

    await user.type(screen.getByLabelText(/symbol/i), 'AAPL');
    await user.type(screen.getByLabelText(/quantity/i), '150');
    await user.click(screen.getByRole('button', { name: /place order/i }));

    expect(screen.getByText(/Maximum quantity is 100/i)).toBeInTheDocument();
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  test('calculates estimated value correctly', async () => {
    const user = userEvent.setup();
    render(<TradeForm onSubmit={mockOnSubmit} currentPrice={150.25} />);

    await user.type(screen.getByLabelText(/quantity/i), '10');

    await waitFor(() => {
      expect(screen.getByTestId('estimated-value')).toHaveTextContent('$1,502.50');
    });
  });

  test('submits valid trade order', async () => {
    const user = userEvent.setup();
    render(<TradeForm onSubmit={mockOnSubmit} />);

    await user.type(screen.getByLabelText(/symbol/i), 'AAPL');
    await user.type(screen.getByLabelText(/quantity/i), '10');
    await user.selectOptions(screen.getByLabelText(/order type/i), 'market');
    await user.click(screen.getByRole('button', { name: /place order/i }));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        symbol: 'AAPL',
        quantity: 10,
        order_type: 'market',
        action: 'buy',
      });
    });
  });
});
```

## 2. MSW (Mock Service Worker) Configuration

### 2.1 Comprehensive Handler Setup

```typescript
// mocks/handlers/portfolio.handlers.ts
import { rest } from 'msw';
import { faker } from '@faker-js/faker';

export const portfolioHandlers = [
  // Portfolio current value
  rest.get('/api/v1/portfolio/current', (req, res, ctx) => {
    const baseValue = 100000;
    const variation = faker.number.float({ min: -0.05, max: 0.05 });
    const currentValue = baseValue * (1 + variation);
    
    return res(
      ctx.status(200),
      ctx.json({
        total_value: currentValue,
        daily_change: currentValue * variation,
        daily_change_percent: variation,
        positions: generateMockPositions(),
        last_updated: new Date().toISOString(),
      })
    );
  }),

  // Portfolio history
  rest.get('/api/v1/portfolio/history', (req, res, ctx) => {
    const days = parseInt(req.url.searchParams.get('days') || '30');
    
    return res(
      ctx.status(200),
      ctx.json({
        history: generateHistoricalData(days),
      })
    );
  }),

  // Rebalance portfolio
  rest.post('/api/v1/portfolio/:id/rebalance', async (req, res, ctx) => {
    const { strategy } = await req.json();
    
    // Simulate processing time
    await ctx.delay(1000);
    
    return res(
      ctx.status(200),
      ctx.json({
        status: 'success',
        changes: generateRebalanceChanges(),
        new_allocations: generateMockAllocations(strategy),
      })
    );
  }),
];

// Helper functions
function generateMockPositions() {
  const symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'];
  return symbols.map(symbol => ({
    symbol,
    shares: faker.number.int({ min: 10, max: 100 }),
    current_price: faker.number.float({ min: 100, max: 3000, precision: 0.01 }),
    total_value: faker.number.float({ min: 5000, max: 50000, precision: 0.01 }),
    daily_change: faker.number.float({ min: -500, max: 500, precision: 0.01 }),
    weight: faker.number.float({ min: 0.1, max: 0.3, precision: 0.001 }),
  }));
}

function generateHistoricalData(days: number) {
  const data = [];
  const startValue = 100000;
  let currentValue = startValue;
  
  for (let i = days; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    
    const dailyReturn = faker.number.float({ min: -0.03, max: 0.03 });
    currentValue = currentValue * (1 + dailyReturn);
    
    data.push({
      date: date.toISOString().split('T')[0],
      value: currentValue,
      daily_return: dailyReturn,
    });
  }
  
  return data;
}
```

### 2.2 Market Data Mocking

```typescript
// mocks/handlers/market.handlers.ts
import { rest } from 'msw';

// Realistic TwelveData response pattern
const generateTwelveDataResponse = (symbol: string) => ({
  meta: {
    symbol,
    interval: '1day',
    currency: 'USD',
    exchange_timezone: 'America/New_York',
    exchange: 'NASDAQ',
    type: 'Common Stock',
  },
  values: [
    {
      datetime: '2024-01-19',
      open: '149.50',
      high: '151.25',
      low: '148.75',
      close: '150.25',
      volume: '58245100',
    },
  ],
  status: 'ok',
});

// Realistic MarketAux response pattern
const generateMarketAuxResponse = () => ({
  meta: {
    found: 10,
    returned: 10,
    limit: 10,
    page: 1,
  },
  data: [
    {
      uuid: faker.string.uuid(),
      title: 'Apple Reports Strong Q4 Earnings',
      description: 'Apple Inc. exceeded analyst expectations...',
      snippet: 'Apple Inc. (AAPL) reported Q4 earnings...',
      url: 'https://example.com/news/apple-q4',
      image_url: 'https://example.com/image.jpg',
      published_at: '2024-01-19T14:30:00Z',
      source: 'Financial Times',
      relevance_score: 0.95,
      entities: [
        {
          symbol: 'AAPL',
          name: 'Apple Inc.',
          exchange: 'NASDAQ',
          sentiment_score: 0.75,
        },
      ],
      similar: [],
    },
  ],
});

export const marketHandlers = [
  rest.get('/api/v1/market/price/:symbol', (req, res, ctx) => {
    const { symbol } = req.params;
    return res(
      ctx.status(200),
      ctx.json(generateTwelveDataResponse(symbol as string))
    );
  }),

  rest.get('/api/v1/news/articles', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json(generateMarketAuxResponse())
    );
  }),
];
```

## 3. E2E Testing with Playwright

### 3.1 Critical User Journeys

```typescript
// e2e/journeys/portfolio-creation.spec.ts
import { test, expect } from '@playwright/test';
import { loginUser, createPortfolio } from '../helpers/actions';

test.describe('Portfolio Creation Journey', () => {
  test.beforeEach(async ({ page }) => {
    await loginUser(page, 'test@example.com', 'Test123!');
  });

  test('complete portfolio creation flow', async ({ page }) => {
    // Navigate to portfolio creation
    await page.goto('/dashboard');
    await page.click('[data-testid="create-portfolio-btn"]');

    // Fill portfolio details
    await page.fill('[name="portfolio_name"]', 'Growth Portfolio');
    await page.fill('[name="initial_value"]', '50000');
    
    // Select strategy
    await page.click('[data-testid="strategy-selector"]');
    await page.click('[data-value="moderate-growth"]');

    // Set risk parameters
    await page.fill('[name="max_drawdown"]', '15');
    await page.fill('[name="target_return"]', '12');

    // Review and confirm
    await page.click('[data-testid="review-portfolio"]');
    
    // Verify preview
    await expect(page.locator('[data-testid="preview-name"]'))
      .toHaveText('Growth Portfolio');
    await expect(page.locator('[data-testid="preview-value"]'))
      .toHaveText('$50,000.00');

    // Create portfolio
    await page.click('[data-testid="confirm-create"]');

    // Wait for redirect
    await page.waitForURL(/\/portfolio\/[a-z0-9-]+/);

    // Verify portfolio created
    await expect(page.locator('h1')).toContainText('Growth Portfolio');
    await expect(page.locator('[data-testid="portfolio-status"]'))
      .toHaveText('Active');
  });

  test('validates minimum investment amount', async ({ page }) => {
    await page.goto('/portfolios/new');
    
    await page.fill('[name="portfolio_name"]', 'Test Portfolio');
    await page.fill('[name="initial_value"]', '100'); // Below minimum

    await page.click('[data-testid="create-portfolio"]');

    await expect(page.locator('[data-testid="error-message"]'))
      .toHaveText('Minimum investment is $1,000');
  });
});
```

### 3.2 Trading Workflow Tests

```typescript
// e2e/journeys/trading-workflow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Trading Workflow', () => {
  test('execute buy order with validation', async ({ page }) => {
    await page.goto('/portfolio/123/trade');

    // Search for stock
    await page.fill('[data-testid="symbol-search"]', 'AAPL');
    await page.waitForSelector('[data-testid="search-results"]');
    await page.click('[data-testid="select-AAPL"]');

    // Verify real-time price display
    await expect(page.locator('[data-testid="current-price"]'))
      .toContainText('$');

    // Enter order details
    await page.fill('[name="quantity"]', '10');
    await page.selectOption('[name="order_type"]', 'limit');
    await page.fill('[name="limit_price"]', '149.50');

    // Verify order summary
    const estimatedCost = await page.locator('[data-testid="estimated-cost"]').textContent();
    expect(estimatedCost).toBe('$1,495.00');

    // Check available balance
    const availableBalance = await page.locator('[data-testid="available-balance"]').textContent();
    expect(parseFloat(availableBalance!.replace(/[$,]/g, ''))).toBeGreaterThan(1495);

    // Place order
    await page.click('[data-testid="place-order"]');

    // Confirm in modal
    await page.click('[data-testid="confirm-order"]');

    // Verify success
    await expect(page.locator('[data-testid="order-status"]'))
      .toHaveText('Order Placed Successfully');
  });

  test('prevent over-leveraging', async ({ page }) => {
    await page.goto('/portfolio/123/trade');

    // Try to buy more than available balance
    await page.fill('[data-testid="symbol-search"]', 'GOOGL');
    await page.click('[data-testid="select-GOOGL"]');
    await page.fill('[name="quantity"]', '1000'); // Excessive quantity

    await page.click('[data-testid="place-order"]');

    // Should show error
    await expect(page.locator('[data-testid="insufficient-funds-error"]'))
      .toBeVisible();
    await expect(page.locator('[data-testid="insufficient-funds-error"]'))
      .toContainText('Insufficient funds');
  });
});
```

## 4. Visual Regression Testing

### 4.1 Percy/Chromatic Setup

```typescript
// tests/visual/dashboard.visual.ts
import { test } from '@playwright/test';
import percySnapshot from '@percy/playwright';

test.describe('Dashboard Visual Tests', () => {
  test('dashboard layout - desktop', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    
    // Hide dynamic content
    await page.evaluate(() => {
      document.querySelectorAll('[data-testid*="price"]').forEach(el => {
        el.textContent = '$100.00';
      });
      document.querySelectorAll('[data-testid*="time"]').forEach(el => {
        el.textContent = '12:00 PM';
      });
    });

    await percySnapshot(page, 'Dashboard - Desktop', {
      widths: [1920, 1440],
    });
  });

  test('dashboard layout - mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    await percySnapshot(page, 'Dashboard - Mobile', {
      widths: [375],
    });
  });

  test('dark mode consistency', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Enable dark mode
    await page.click('[data-testid="theme-toggle"]');
    await page.waitForTimeout(500); // Wait for transition

    await percySnapshot(page, 'Dashboard - Dark Mode', {
      widths: [1920],
    });
  });

  test('chart visualizations', async ({ page }) => {
    await page.goto('/dashboard/analytics');
    await page.waitForSelector('[data-testid="portfolio-chart"]');

    // Stabilize chart animations
    await page.evaluate(() => {
      const charts = document.querySelectorAll('canvas, svg');
      charts.forEach(chart => {
        chart.style.animation = 'none';
      });
    });

    await percySnapshot(page, 'Analytics Charts', {
      widths: [1920],
    });
  });
});
```

## 5. Performance Testing

### 5.1 Component Performance

```typescript
// tests/performance/component-performance.test.tsx
import { render } from '@testing-library/react';
import { measureRender } from '@/tests/utils/performance';
import { PortfolioDashboard } from '@/components/PortfolioDashboard';

describe('Component Performance', () => {
  test('PortfolioDashboard renders within 16ms', () => {
    const mockData = generateLargePortfolioData(100); // 100 positions
    
    const renderTime = measureRender(
      <PortfolioDashboard data={mockData} />
    );

    expect(renderTime).toBeLessThan(16); // One frame at 60fps
  });

  test('Large table renders efficiently with virtualization', () => {
    const rows = generateTableData(10000); // 10k rows
    
    const renderTime = measureRender(
      <VirtualizedTable data={rows} />
    );

    expect(renderTime).toBeLessThan(100); // Should use virtualization
  });

  test('Real-time updates dont cause layout thrashing', () => {
    const { rerender } = render(<PriceTicket symbol="AAPL" />);
    
    const updates = 100;
    const startTime = performance.now();
    
    for (let i = 0; i < updates; i++) {
      rerender(<PriceTicket symbol="AAPL" price={150 + i * 0.01} />);
    }
    
    const totalTime = performance.now() - startTime;
    const avgUpdateTime = totalTime / updates;
    
    expect(avgUpdateTime).toBeLessThan(1); // <1ms per update
  });
});
```

## 6. Test Utilities

### 6.1 Custom Test Utilities

```typescript
// tests/utils/test-utils.tsx
import { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/contexts/AuthContext';
import { ThemeProvider } from '@/contexts/ThemeContext';

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      cacheTime: 0,
    },
  },
});

interface TestUser {
  id: string;
  email: string;
  name: string;
  roles: string[];
}

const AllTheProviders = ({ 
  children,
  user,
}: { 
  children: React.ReactNode;
  user?: TestUser;
}) => {
  const queryClient = createTestQueryClient();
  
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider initialUser={user}>
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
};

const customRender = (
  ui: ReactElement,
  {
    user,
    ...options
  }: RenderOptions & { user?: TestUser } = {}
) => render(ui, { 
  wrapper: (props) => <AllTheProviders {...props} user={user} />,
  ...options 
});

export * from '@testing-library/react';
export { customRender as render };
```

### 6.2 Test Data Builders

```typescript
// tests/builders/portfolio.builder.ts
import { faker } from '@faker-js/faker';

export class PortfolioBuilder {
  private portfolio = {
    id: faker.string.uuid(),
    name: 'Test Portfolio',
    total_value: 100000,
    daily_change: 0,
    daily_change_percent: 0,
    positions: [],
    created_at: new Date().toISOString(),
  };

  withId(id: string) {
    this.portfolio.id = id;
    return this;
  }

  withName(name: string) {
    this.portfolio.name = name;
    return this;
  }

  withValue(value: number) {
    this.portfolio.total_value = value;
    return this;
  }

  withPositions(count: number) {
    this.portfolio.positions = Array.from({ length: count }, () => ({
      symbol: faker.helpers.arrayElement(['AAPL', 'GOOGL', 'MSFT', 'AMZN']),
      shares: faker.number.int({ min: 10, max: 100 }),
      value: faker.number.float({ min: 1000, max: 10000 }),
    }));
    return this;
  }

  withGain(percent: number) {
    this.portfolio.daily_change_percent = percent;
    this.portfolio.daily_change = this.portfolio.total_value * percent;
    return this;
  }

  build() {
    return this.portfolio;
  }
}

// Usage
const portfolio = new PortfolioBuilder()
  .withName('Growth Portfolio')
  .withValue(150000)
  .withPositions(10)
  .withGain(0.025)
  .build();
```

## 7. CI/CD Integration

### 7.1 Frontend Test Pipeline

```yaml
# .github/workflows/frontend-tests.yml
name: Frontend Tests

on:
  push:
    paths:
      - 'apps/web/**'
      - '.github/workflows/frontend-tests.yml'

jobs:
  unit-tests:
    name: Unit & Component Tests
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci --workspace=apps/web
      
      - name: Run tests with coverage
        run: |
          npm run test:coverage --workspace=apps/web
          
      - name: Check coverage threshold
        run: |
          coverage=$(cat apps/web/coverage/coverage-summary.json | jq '.total.lines.pct')
          if (( $(echo "$coverage < 90" | bc -l) )); then
            echo "Coverage $coverage% is below 90% threshold"
            exit 1
          fi
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./apps/web/coverage/lcov.info
          flags: frontend

  e2e-tests:
    name: E2E Tests
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Playwright
        run: npx playwright install --with-deps
      
      - name: Run E2E tests
        run: npm run test:e2e --workspace=apps/web
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: apps/web/playwright-report

  visual-tests:
    name: Visual Regression Tests
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Percy tests
        env:
          PERCY_TOKEN: ${{ secrets.PERCY_TOKEN }}
        run: |
          npm run test:visual --workspace=apps/web
```

## Summary

This frontend testing specification ensures:
- **90%+ component coverage** with React Testing Library
- **Realistic API mocking** with MSW matching TwelveData/MarketAux patterns
- **Critical path E2E testing** with Playwright
- **Visual regression testing** for UI consistency
- **Performance testing** for responsive UX
- **CI/CD integration** with coverage gates

All tests focus on financial accuracy, user workflow integrity, and visual consistency for a production-grade trading platform.