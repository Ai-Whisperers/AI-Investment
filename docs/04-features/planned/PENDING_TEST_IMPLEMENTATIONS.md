# Pending Test Implementations

## Overview
This document tracks test cases that are currently skipped or failing due to unimplemented features. These tests serve as specifications for future feature development.

**Last Updated**: 2025-08-20  
**Total Pending**: 5 tests (2 skipped, 3 failing)

## 1. Admin Endpoints (2 tests skipped)

### Location
`apps/api/tests/unit/routers/test_auth.py::TestAuthEndpoints::test_admin_endpoint_access`

### Status
- **Type**: Skipped
- **Reason**: Admin endpoints not yet implemented
- **Impact**: Non-critical - admin functionality not required for MVP

### Implementation Requirements
```python
# Required endpoints:
GET /api/v1/admin/users       # List all users
GET /api/v1/admin/users/{id}  # Get user details
PUT /api/v1/admin/users/{id}  # Update user
DELETE /api/v1/admin/users/{id} # Delete user
GET /api/v1/admin/portfolios  # List all portfolios
GET /api/v1/admin/metrics     # System metrics

# Required features:
- Admin role in User model
- Role-based access control (RBAC)
- Admin-only dependency injection
- Admin dashboard UI
```

### Test Expectations
```python
def test_admin_endpoint_access(self, client, auth_headers, admin_auth_headers):
    # Regular user should be denied (403 Forbidden)
    response = client.get("/api/v1/admin/users", headers=auth_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    # Admin should have access (200 OK)
    response = client.get("/api/v1/admin/users", headers=admin_auth_headers)
    assert response.status_code == status.HTTP_200_OK
```

### Implementation Priority
**LOW** - Admin features can be added after core functionality is stable

---

## 2. Rate Limiting (1 test skipped)

### Location
`apps/api/tests/unit/routers/test_auth.py::TestAuthEndpoints::test_rate_limiting`

### Status
- **Type**: Skipped
- **Reason**: Rate limiting middleware not implemented
- **Impact**: Medium - important for production security

### Implementation Requirements
```python
# Required middleware:
- Redis-based rate limiter
- Configurable limits per endpoint
- IP-based and user-based limits
- Graceful degradation if Redis unavailable

# Configuration:
RATE_LIMIT_PER_MINUTE = 60      # Default
AUTH_RATE_LIMIT_PER_MINUTE = 10 # Login/register
API_RATE_LIMIT_PER_MINUTE = 100 # API calls

# Response headers:
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640995200
```

### Test Expectations
```python
def test_rate_limiting(self, client):
    # Attempt 10 rapid login attempts
    for i in range(10):
        response = client.post("/api/v1/auth/login", json={...})
    
    # 11th attempt should be rate limited
    response = client.post("/api/v1/auth/login", json={...})
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "X-RateLimit-Remaining" in response.headers
```

### Implementation Priority
**MEDIUM** - Should be implemented before production deployment

### Recommended Libraries
- `slowapi` - Starlette/FastAPI rate limiting
- `redis-py` - Redis client for distributed rate limiting
- Custom middleware using Redis INCR with TTL

---

## 3. Momentum Strategy in Weight Calculator (3 tests failing)

### Location
```
apps/api/tests/unit/services/test_weight_calculator.py::TestWeightCalculator::test_weight_calculation_methods[momentum-expected_range1]
apps/api/tests/unit/services/test_weight_calculator.py::TestWeightCalculator::test_calculate_momentum_weights
apps/api/tests/unit/services/test_weight_calculator.py::TestWeightCalculator::test_apply_weight_constraints
```

### Status
- **Type**: Failing
- **Reason**: Momentum strategy calculation incomplete
- **Impact**: Low - alternative strategies available

### Implementation Requirements
```python
class WeightCalculator:
    def calculate_momentum_weights(
        self,
        price_data: pd.DataFrame,
        lookback_period: int = 30,
        top_n: int = None
    ) -> Dict[str, float]:
        """
        Calculate weights based on momentum (price performance).
        
        Algorithm:
        1. Calculate returns over lookback period
        2. Rank assets by performance
        3. Weight proportionally to momentum score
        4. Optional: Select only top N performers
        """
        # Calculate momentum scores
        momentum_scores = {}
        for symbol in price_data.columns:
            prices = price_data[symbol].dropna()
            if len(prices) >= lookback_period:
                momentum = (prices.iloc[-1] / prices.iloc[-lookback_period] - 1)
                momentum_scores[symbol] = max(0, momentum)  # Long-only
        
        # Convert to weights
        total_score = sum(momentum_scores.values())
        if total_score > 0:
            weights = {k: v/total_score for k, v in momentum_scores.items()}
        else:
            # Equal weight if no positive momentum
            weights = {k: 1/len(momentum_scores) for k in momentum_scores}
        
        return weights
```

### Test Expectations
```python
def test_calculate_momentum_weights(self, calculator, sample_data):
    # Add trend to create momentum
    sample_data['AAPL'] += np.linspace(0, 10, len(sample_data))  # Strong uptrend
    sample_data['GOOGL'] -= np.linspace(0, 5, len(sample_data))  # Downtrend
    
    weights = calculator.calculate_momentum_weights(sample_data)
    
    # AAPL should have highest weight (positive momentum)
    assert weights['AAPL'] > weights['MSFT']
    assert weights['AAPL'] > weights['GOOGL']
    
    # Weights should sum to 1
    assert sum(weights.values()) == pytest.approx(1.0)
```

### Implementation Priority
**LOW** - Core equal-weight and market-cap strategies working

---

## Implementation Plan

### Phase 1: Security & Stability (Q1 2025)
1. **Rate Limiting** - Protect API from abuse
   - Implement Redis-based rate limiter
   - Add configurable limits
   - Test with load testing tools

### Phase 2: Advanced Features (Q2 2025)
2. **Admin Functionality** - System management
   - Design RBAC system
   - Implement admin endpoints
   - Create admin dashboard UI

3. **Momentum Strategy** - Enhanced portfolio optimization
   - Complete momentum calculations
   - Add backtesting for validation
   - Integrate with existing strategies

## Testing Philosophy

These pending tests represent our commitment to Test-Driven Development (TDD):
1. Tests are written first as specifications
2. Features are implemented to make tests pass
3. Tests serve as living documentation
4. Skipped tests track technical debt

## Monitoring Progress

Track implementation progress:
```bash
# Check skipped tests
pytest -v -m "skip" --tb=no

# Check specific pending features
pytest -k "admin" -v
pytest -k "rate_limit" -v
pytest -k "momentum" -v

# Generate coverage report
pytest --cov=app --cov-report=html
```

## Related Documentation
- [Testing Strategy](../../03-implementation/backend/testing/TESTING_STRATEGY.md)
- [Roadmap](../../05-roadmap/README.md)
- [API Reference](../../02-api-reference/README.md)