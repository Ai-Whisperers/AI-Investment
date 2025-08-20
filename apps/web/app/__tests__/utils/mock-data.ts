/**
 * Mock data generators for tests
 * Single responsibility: Generate test data
 * Avoid creating god objects by separating concerns
 */

export const mockUser = {
  id: 1,
  email: 'test@example.com',
  created_at: '2024-01-01T00:00:00Z',
}

export const mockPortfolio = {
  id: 1,
  name: 'Test Portfolio',
  total_value: 100000,
  returns: 0.15,
  strategy_config: {
    strategy_type: 'balanced',
    rebalance_frequency: 'monthly',
  },
}

export const mockAsset = {
  symbol: 'AAPL',
  name: 'Apple Inc.',
  sector: 'Technology',
  current_price: 150.00,
  daily_change: 0.02,
}

export const mockDiagnostics = {
  database: {
    status: 'healthy',
    connection_count: 5,
    response_time_ms: 25,
  },
  cache: {
    status: 'healthy',
    hit_rate: 0.85,
    memory_usage_mb: 128,
  },
  api: {
    status: 'healthy',
    uptime_seconds: 86400,
    request_count: 1000,
  },
}

// Factory functions for dynamic data
export function createMockPriceData(days: number = 30) {
  const data = []
  const startDate = new Date()
  startDate.setDate(startDate.getDate() - days)
  
  for (let i = 0; i < days; i++) {
    const date = new Date(startDate)
    date.setDate(date.getDate() + i)
    
    data.push({
      date: date.toISOString().split('T')[0],
      value: 100000 + Math.random() * 10000,
      benchmark: 95000 + Math.random() * 10000,
    })
  }
  
  return data
}

export function createMockAllocations(count: number = 5) {
  const symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
  const allocations = []
  
  for (let i = 0; i < Math.min(count, symbols.length); i++) {
    allocations.push({
      symbol: symbols[i],
      weight: (1 / count),
      value: 100000 / count,
    })
  }
  
  return allocations
}