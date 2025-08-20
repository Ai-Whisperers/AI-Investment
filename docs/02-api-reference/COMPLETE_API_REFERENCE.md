# Waardhaven AutoIndex API Reference

## Table of Contents
- [Overview](#overview)
- [Authentication](#authentication)
- [Base URLs & Configuration](#base-urls--configuration)
- [Request/Response Format](#requestresponse-format)
- [API Endpoints](#api-endpoints)
  - [Authentication](#authentication-endpoints)
  - [Portfolio Index](#portfolio-index-endpoints)
  - [Portfolio Calculations](#portfolio-calculations-endpoints)
  - [Benchmark](#benchmark-endpoints)
  - [Strategy](#strategy-endpoints)
  - [News & Sentiment](#news--sentiment-endpoints)
  - [Background Tasks](#background-tasks-endpoints)
  - [Diagnostics](#diagnostics-endpoints)
  - [Manual Operations](#manual-operations-endpoints)
- [Schemas](#schemas)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Integration Notes](#integration-notes)

## Overview

The Waardhaven AutoIndex API is a production-ready investment portfolio management system providing:

- **Portfolio Management**: Automated index creation and strategy optimization
- **Real-time Data**: Market data integration with TwelveData
- **News & Sentiment**: Financial news analysis with Marketaux
- **Background Processing**: Async tasks with Celery and Redis
- **Performance Analytics**: Risk metrics and benchmark comparison
- **Clean Architecture**: Modular provider pattern with circuit breakers

### Technology Stack
- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with TimescaleDB for time-series
- **Cache**: Redis for performance optimization
- **Queue**: Celery + RabbitMQ for background tasks
- **Authentication**: JWT with bcrypt password hashing

## Authentication

All API endpoints except health checks require JWT authentication.

### Token Usage
Include the JWT token in the Authorization header:
```http
Authorization: Bearer <access_token>
```

### Token Lifecycle
- **Access Token**: Valid for 30 minutes
- **Refresh Token**: Valid for 7 days
- **Automatic Refresh**: Frontend handles token renewal

## Base URLs & Configuration

### Production
- **API**: `https://waardhaven-api.onrender.com`
- **Documentation**: `https://waardhaven-api.onrender.com/docs`
- **Health**: `https://waardhaven-api.onrender.com/health`

### Local Development
- **API**: `http://localhost:8000`
- **Documentation**: `http://localhost:8000/docs`
- **Health**: `http://localhost:8000/health`

### API Versioning
- Current version: `v1`
- Base path: `/api/v1/`
- Deprecation notice: 6 months
- Sunset period: 12 months

## Request/Response Format

### Content Types
- **Request**: `application/json`
- **Response**: `application/json`
- **Encoding**: UTF-8

### Date Formats
- **Date**: ISO 8601 (`YYYY-MM-DD`)
- **DateTime**: ISO 8601 with timezone (`YYYY-MM-DDTHH:MM:SSZ`)

### Pagination
For list endpoints:
- `limit`: Number of items (default: 50, max: 100)
- `offset`: Skip items (default: 0)
- `sort`: Sort field (e.g., "date", "-value")

## API Endpoints

### Authentication Endpoints

Base path: `/api/v1/auth`

#### POST /api/v1/auth/register
**Description**: Register new user  
**Authentication**: None  
**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "username": "optional_username"
}
```
**Response**:
```json
{
  "message": "User created successfully",
  "user_id": 1
}
```
**Validation**:
- Email must be valid format
- Password minimum 8 characters with uppercase, lowercase, number

#### POST /api/v1/auth/login
**Description**: User login with email/password  
**Authentication**: None  
**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```
**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### POST /api/v1/auth/google
**Description**: Google OAuth authentication  
**Authentication**: None  
**Request Body**:
```json
{
  "credential": "google-oauth-id-token"
}
```
**Response**: Same as login

#### GET /api/v1/auth/me
**Description**: Get current user information  
**Authentication**: Required  
**Response**:
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "user123",
  "is_google_user": false,
  "created_at": "2025-01-19T12:00:00Z",
  "last_login": "2025-01-19T14:30:00Z"
}
```

#### POST /api/v1/auth/refresh
**Description**: Refresh access token  
**Authentication**: None  
**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### POST /api/v1/auth/logout
**Description**: Logout user (invalidate tokens)  
**Authentication**: Required  
**Response**:
```json
{
  "message": "Successfully logged out"
}
```

### Portfolio Index Endpoints

Base path: `/api/v1/index`

#### GET /api/v1/index/values
**Description**: Get portfolio index values with optional date filtering  
**Authentication**: Required  
**Query Parameters**:
- `start_date` (optional): ISO date string (YYYY-MM-DD)
- `end_date` (optional): ISO date string (YYYY-MM-DD)
- `limit` (optional): Number of records (default: 250, max: 1000)
- `offset` (optional): Skip records for pagination

**Response**:
```json
{
  "values": [
    {
      "date": "2025-01-19",
      "value": 1050.25,
      "daily_return": 0.0125,
      "total_return": 0.0502,
      "volume": 1250000
    },
    {
      "date": "2025-01-18",
      "value": 1037.23,
      "daily_return": 0.0089,
      "total_return": 0.0372,
      "volume": 1180000
    }
  ],
  "metadata": {
    "count": 250,
    "start_date": "2024-01-01",
    "end_date": "2025-01-19",
    "initial_value": 1000.0
  }
}
```

#### POST /api/v1/index/compute
**Description**: Compute index values for specified date range  
**Authentication**: Required  
**Request Body**:
```json
{
  "start_date": "2024-01-01",
  "end_date": "2025-01-19",
  "initial_value": 1000,
  "force_recompute": false
}
```
**Response**:
```json
{
  "message": "Index computation completed successfully",
  "records_created": 250,
  "records_updated": 15,
  "date_range": {
    "start": "2024-01-01",
    "end": "2025-01-19"
  },
  "computation_time_seconds": 12.5
}
```

#### GET /api/v1/index/performance
**Description**: Get comprehensive performance metrics  
**Authentication**: Required  
**Query Parameters**:
- `period` (optional): "1D", "1W", "1M", "3M", "6M", "1Y", "YTD", "ALL"

**Response**:
```json
{
  "period": "1Y",
  "returns": {
    "daily": 0.0012,
    "weekly": 0.0085,
    "monthly": 0.0342,
    "quarterly": 0.1134,
    "yearly": 0.1523,
    "ytd": 0.0523
  },
  "risk_metrics": {
    "volatility": 0.1823,
    "sharpe_ratio": 1.45,
    "sortino_ratio": 1.82,
    "calmar_ratio": 1.34,
    "max_drawdown": -0.0823,
    "current_drawdown": -0.0145,
    "var_95": -0.0234,
    "var_99": -0.0367,
    "beta_sp500": 0.89,
    "correlation_sp500": 0.76
  },
  "statistics": {
    "best_day": 0.0453,
    "worst_day": -0.0367,
    "positive_days": 145,
    "negative_days": 105,
    "win_rate": 0.58,
    "average_win": 0.0156,
    "average_loss": -0.0134
  }
}
```

#### GET /api/v1/index/allocations
**Description**: Get current portfolio allocations and holdings  
**Authentication**: Required  
**Query Parameters**:
- `as_of_date` (optional): Get allocations as of specific date

**Response**:
```json
{
  "as_of_date": "2025-01-19",
  "allocations": [
    {
      "asset_id": 1,
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "sector": "Technology",
      "weight": 0.15,
      "value": 15000,
      "shares": 100.5,
      "price": 149.25,
      "change": 0.0234,
      "market_cap": 2400000000000
    },
    {
      "asset_id": 2,
      "symbol": "MSFT",
      "name": "Microsoft Corporation",
      "sector": "Technology",
      "weight": 0.12,
      "value": 12000,
      "shares": 85.2,
      "price": 140.85,
      "change": 0.0156,
      "market_cap": 2100000000000
    }
  ],
  "summary": {
    "total_value": 100000,
    "asset_count": 25,
    "sector_breakdown": {
      "Technology": 0.45,
      "Healthcare": 0.15,
      "Finance": 0.20,
      "Consumer": 0.12,
      "Energy": 0.08
    },
    "last_rebalance": "2025-01-15T09:00:00Z",
    "next_rebalance": "2025-02-15T09:00:00Z"
  }
}
```

#### POST /api/v1/index/rebalance
**Description**: Trigger portfolio rebalancing  
**Authentication**: Required  
**Request Body**:
```json
{
  "force": false,
  "dry_run": true,
  "target_date": "2025-01-20"
}
```
**Response**:
```json
{
  "rebalance_id": "rb_12345",
  "status": "completed",
  "changes": [
    {
      "symbol": "AAPL",
      "current_weight": 0.15,
      "target_weight": 0.12,
      "shares_to_sell": 15.5
    }
  ],
  "execution_cost": 25.50,
  "expected_impact": 0.0012
}
```

### Portfolio Calculations Endpoints

Base path: `/api/v1/portfolio/calculations`

**NEW (2025-08-20)**: Backend calculation services replacing frontend calculations for consistency and performance.

#### POST /api/v1/portfolio/calculations/returns
**Description**: Calculate daily returns from price series  
**Authentication**: Required  
**Request Body**:
```json
{
  "values": [100, 105, 102, 108, 110, 95, 98, 103, 107, 109]
}
```

**Response**:
```json
{
  "returns": [0.05, -0.0286, 0.0588, 0.0185, -0.1364, 0.0316, 0.0510, 0.0388, 0.0187]
}
```

#### POST /api/v1/portfolio/calculations/total-return
**Description**: Calculate total return between two values  
**Authentication**: Required  
**Request Body**:
```json
{
  "start_value": 100,
  "end_value": 109
}
```

**Response**:
```json
{
  "total_return": 9.0
}
```

#### POST /api/v1/portfolio/calculations/annualized-return
**Description**: Calculate annualized return from total return and period  
**Authentication**: Required  
**Request Body**:
```json
{
  "total_return": 9.0,
  "period_in_days": 252
}
```

**Response**:
```json
{
  "annualized_return": 9.23
}
```

#### POST /api/v1/portfolio/calculations/volatility
**Description**: Calculate annualized volatility from returns  
**Authentication**: Required  
**Request Body**:
```json
{
  "returns": [0.05, -0.0286, 0.0588, 0.0185, -0.1364, 0.0316, 0.0510, 0.0388, 0.0187]
}
```

**Response**:
```json
{
  "volatility": 91.66
}
```

#### POST /api/v1/portfolio/calculations/sharpe-ratio
**Description**: Calculate Sharpe ratio  
**Authentication**: Required  
**Request Body**:
```json
{
  "annualized_return": 9.23,
  "volatility": 91.66,
  "risk_free_rate": 2.0
}
```

**Response**:
```json
{
  "sharpe_ratio": 0.079
}
```

#### POST /api/v1/portfolio/calculations/max-drawdown
**Description**: Calculate maximum and current drawdown  
**Authentication**: Required  
**Request Body**:
```json
{
  "values": [100, 105, 102, 108, 110, 95, 98, 103, 107, 109]
}
```

**Response**:
```json
{
  "max_drawdown": 13.64,
  "current_drawdown": 0.93
}
```

#### POST /api/v1/portfolio/calculations/portfolio-metrics
**Description**: Calculate comprehensive portfolio performance metrics  
**Authentication**: Required  
**Request Body**:
```json
{
  "values": [100, 105, 102, 108, 110, 95, 98, 103, 107, 109],
  "period_in_days": 10
}
```

**Response**:
```json
{
  "metrics": {
    "total_return": 9.0,
    "annualized_return": 9.23,
    "volatility": 91.66,
    "sharpe_ratio": 0.079,
    "max_drawdown": 13.64,
    "current_drawdown": 0.93
  }
}
```

**Features**:
- ✅ **Production Algorithms**: Using scipy for accurate financial calculations
- ✅ **Error Handling**: Comprehensive validation and graceful error responses
- ✅ **Consistency**: Same algorithms used across all client applications
- ✅ **Performance**: Server-side calculations with optimized algorithms
- ✅ **Validation**: Input validation and business rule enforcement

### Benchmark Endpoints

Base path: `/api/v1/benchmark`

#### GET /api/v1/benchmark/sp500
**Description**: Get S&P 500 benchmark data  
**Authentication**: Required  
**Query Parameters**:
- `start_date` (optional): ISO date string
- `end_date` (optional): ISO date string
- `normalize` (optional): Normalize to base 100 (default: false)

**Response**:
```json
{
  "data": [
    {
      "date": "2025-01-19",
      "close": 4823.15,
      "open": 4810.25,
      "high": 4835.67,
      "low": 4802.33,
      "volume": 3250000000,
      "return": 0.0023,
      "normalized_value": 102.3
    }
  ],
  "performance": {
    "total_return": 0.1234,
    "annualized_return": 0.1156,
    "volatility": 0.1456,
    "sharpe_ratio": 1.23,
    "max_drawdown": -0.0892
  },
  "metadata": {
    "count": 250,
    "start_date": "2024-01-01",
    "end_date": "2025-01-19"
  }
}
```

#### GET /api/v1/benchmark/comparison
**Description**: Compare portfolio performance vs S&P 500  
**Authentication**: Required  
**Query Parameters**:
- `period` (optional): Time period for comparison

**Response**:
```json
{
  "period": "1Y",
  "portfolio": {
    "return": 0.1523,
    "volatility": 0.1823,
    "sharpe": 1.45,
    "max_drawdown": -0.0823,
    "beta": 0.89
  },
  "benchmark": {
    "return": 0.1234,
    "volatility": 0.1456,
    "sharpe": 1.23,
    "max_drawdown": -0.0892,
    "beta": 1.0
  },
  "relative_performance": {
    "excess_return": 0.0289,
    "tracking_error": 0.0456,
    "information_ratio": 0.63,
    "up_capture": 1.08,
    "down_capture": 0.92,
    "correlation": 0.76
  },
  "time_series": [
    {
      "date": "2025-01-19",
      "portfolio_return": 0.1523,
      "benchmark_return": 0.1234,
      "excess_return": 0.0289
    }
  ]
}
```

### Strategy Endpoints

Base path: `/api/v1/strategy`

#### GET /api/v1/strategy/config
**Description**: Get current strategy configuration  
**Authentication**: Required  
**Response**:
```json
{
  "id": 1,
  "name": "Balanced Growth Strategy",
  "description": "Momentum and market cap weighted with risk parity",
  "weights": {
    "momentum_weight": 0.4,
    "market_cap_weight": 0.3,
    "risk_parity_weight": 0.3
  },
  "parameters": {
    "rebalance_frequency": "MONTHLY",
    "lookback_period": 30,
    "min_weight": 0.01,
    "max_weight": 0.20,
    "target_assets": 20
  },
  "risk_controls": {
    "daily_drop_threshold": -0.01,
    "max_daily_return": 0.05,
    "min_daily_return": -0.05,
    "min_price_threshold": 1.0
  },
  "optimization": {
    "method": "MEAN_VARIANCE",
    "risk_level": "MODERATE"
  },
  "created_at": "2024-12-01T10:00:00Z",
  "updated_at": "2025-01-15T14:30:00Z",
  "is_active": true
}
```

#### POST /api/v1/strategy/update
**Description**: Update strategy configuration  
**Authentication**: Required  
**Request Body**:
```json
{
  "name": "Enhanced Growth Strategy",
  "weights": {
    "momentum_weight": 0.5,
    "market_cap_weight": 0.3,
    "risk_parity_weight": 0.2
  },
  "parameters": {
    "rebalance_frequency": "QUARTERLY",
    "max_weight": 0.15
  },
  "risk_controls": {
    "risk_level": "AGGRESSIVE"
  }
}
```
**Validation**:
- Weights must sum to 1.0
- All weights between 0 and 1
- Valid rebalance frequency values
**Response**:
```json
{
  "message": "Strategy updated successfully",
  "config": {
    // Updated configuration object
  },
  "validation_results": {
    "weights_valid": true,
    "parameters_valid": true,
    "backtest_score": 0.85
  }
}
```

#### POST /api/v1/strategy/backtest
**Description**: Run comprehensive strategy backtest  
**Authentication**: Required  
**Request Body**:
```json
{
  "start_date": "2023-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 100000,
  "benchmark": "SPY",
  "config": {
    "momentum_weight": 0.6,
    "market_cap_weight": 0.4,
    "rebalance_frequency": "MONTHLY"
  },
  "transaction_costs": 0.001,
  "slippage": 0.0005
}
```
**Response**:
```json
{
  "backtest_id": "bt_67890",
  "results": {
    "performance": {
      "total_return": 0.2345,
      "annual_return": 0.1156,
      "volatility": 0.1823,
      "sharpe_ratio": 1.56,
      "sortino_ratio": 1.89,
      "max_drawdown": -0.1234,
      "calmar_ratio": 1.23
    },
    "trading": {
      "total_trades": 48,
      "winning_trades": 28,
      "losing_trades": 20,
      "win_rate": 0.583,
      "average_trade": 0.0089,
      "transaction_costs": 245.67
    },
    "risk_analysis": {
      "var_95": -0.0234,
      "expected_shortfall": -0.0345,
      "beta": 0.87,
      "correlation": 0.76
    }
  },
  "equity_curve": [
    {
      "date": "2023-01-01",
      "portfolio_value": 100000,
      "benchmark_value": 100000,
      "drawdown": 0.0
    }
  ],
  "trades": [
    {
      "date": "2023-01-15",
      "symbol": "AAPL",
      "action": "BUY",
      "shares": 50,
      "price": 150.25,
      "cost": 7512.50
    }
  ],
  "execution_time": 15.2
}
```

### News & Sentiment Endpoints

Base path: `/api/v1/news`

#### GET /api/v1/news/search
**Description**: Search financial news with advanced filtering  
**Authentication**: Required  
**Query Parameters**:
- `symbols` (optional): Comma-separated stock symbols
- `keywords` (optional): Search keywords (supports AND, OR operators)
- `sentiment_min` (optional): Minimum sentiment (-1 to 1)
- `sentiment_max` (optional): Maximum sentiment (-1 to 1)
- `published_after` (optional): ISO datetime
- `published_before` (optional): ISO datetime
- `sources` (optional): Comma-separated news sources
- `languages` (optional): Language codes (en, es, fr, etc.)
- `limit` (optional): Results per page (default: 20, max: 100)
- `offset` (optional): Pagination offset
- `sort` (optional): Sort order (published_at, sentiment, relevance)

**Response**:
```json
{
  "articles": [
    {
      "id": "art_12345",
      "title": "Apple Reports Strong Q4 Earnings",
      "description": "Apple Inc. exceeded analyst expectations...",
      "url": "https://example.com/article",
      "published_at": "2025-01-19T12:00:00Z",
      "source": {
        "name": "Reuters",
        "domain": "reuters.com",
        "logo_url": "https://reuters.com/logo.png"
      },
      "symbols": ["AAPL", "NASDAQ:AAPL"],
      "entities": [
        {
          "name": "Apple Inc.",
          "type": "company",
          "symbol": "AAPL",
          "sentiment": 0.65,
          "relevance": 0.95
        }
      ],
      "sentiment": {
        "score": 0.65,
        "label": "positive",
        "confidence": 0.89
      },
      "categories": ["earnings", "technology"],
      "language": "en",
      "relevance_score": 0.92
    }
  ],
  "metadata": {
    "total": 1250,
    "count": 20,
    "offset": 0,
    "has_more": true,
    "search_time_ms": 45
  },
  "filters_applied": {
    "symbols": ["AAPL"],
    "sentiment_min": 0.5,
    "date_range": "2025-01-01 to 2025-01-19"
  }
}
```

#### GET /api/v1/news/article/{article_id}
**Description**: Get detailed article information  
**Authentication**: Required  
**Response**:
```json
{
  "id": "art_12345",
  "title": "Apple Reports Strong Q4 Earnings",
  "description": "Full article description...",
  "content": "Complete article content...",
  "url": "https://example.com/article",
  "published_at": "2025-01-19T12:00:00Z",
  "updated_at": "2025-01-19T12:15:00Z",
  "source": {
    "name": "Reuters",
    "domain": "reuters.com",
    "trust_score": 0.95
  },
  "author": "John Doe",
  "entities": [/* entity details */],
  "sentiment": {/* sentiment analysis */},
  "related_articles": [
    {
      "id": "art_12346",
      "title": "Related article title",
      "similarity": 0.78
    }
  ],
  "social_metrics": {
    "shares": 1250,
    "likes": 890,
    "comments": 45
  }
}
```

#### GET /api/v1/news/sentiment/{symbol}
**Description**: Get sentiment analysis for specific symbol over time  
**Authentication**: Required  
**Query Parameters**:
- `days` (optional): Number of days to analyze (default: 30, max: 365)
- `granularity` (optional): daily, hourly (default: daily)

**Response**:
```json
{
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "period": {
    "start_date": "2024-12-20",
    "end_date": "2025-01-19",
    "days": 30
  },
  "current_sentiment": {
    "score": 0.45,
    "label": "positive",
    "confidence": 0.78,
    "last_updated": "2025-01-19T14:00:00Z"
  },
  "aggregates": {
    "average_sentiment": 0.42,
    "sentiment_trend": "improving",
    "volatility": 0.23,
    "article_count": 156
  },
  "distribution": {
    "positive": 0.48,
    "neutral": 0.32,
    "negative": 0.20
  },
  "time_series": [
    {
      "date": "2025-01-19",
      "sentiment_score": 0.45,
      "article_count": 12,
      "confidence": 0.78,
      "top_topics": ["earnings", "iphone"]
    }
  ],
  "top_sources": [
    {
      "source": "Reuters",
      "article_count": 25,
      "average_sentiment": 0.52
    }
  ],
  "trending_topics": [
    {
      "topic": "earnings",
      "count": 23,
      "sentiment": 0.67,
      "trend": "rising"
    }
  ]
}
```

#### GET /api/v1/news/trending
**Description**: Get trending entities and topics  
**Authentication**: Required  
**Query Parameters**:
- `entity_type` (optional): company, person, location, etc.
- `time_range` (optional): 1h, 24h, 7d, 30d (default: 24h)
- `min_articles` (optional): Minimum article count (default: 5)
- `limit` (optional): Number of results (default: 20, max: 100)

**Response**:
```json
{
  "trending_entities": [
    {
      "name": "Apple Inc.",
      "symbol": "AAPL",
      "type": "company",
      "article_count": 45,
      "sentiment": 0.65,
      "trend_score": 0.89,
      "change_24h": 0.15,
      "mentions_growth": 2.3
    }
  ],
  "trending_topics": [
    {
      "topic": "artificial intelligence",
      "article_count": 123,
      "sentiment": 0.52,
      "related_symbols": ["NVDA", "MSFT", "GOOGL"],
      "trend_score": 0.76
    }
  ],
  "metadata": {
    "time_range": "24h",
    "last_updated": "2025-01-19T14:00:00Z",
    "total_articles_analyzed": 15678
  }
}
```

#### POST /api/v1/news/refresh
**Description**: Trigger news data refresh  
**Authentication**: Required  
**Request Body**:
```json
{
  "symbols": ["AAPL", "MSFT", "GOOGL"],
  "keywords": ["earnings", "merger"],
  "force": false,
  "max_articles": 1000
}
```
**Response**:
```json
{
  "task_id": "news_refresh_abc123",
  "status": "queued",
  "message": "News refresh initiated",
  "expected_completion": "2025-01-19T14:05:00Z",
  "scope": {
    "symbols": ["AAPL", "MSFT", "GOOGL"],
    "estimated_articles": 500
  }
}
```

### Background Tasks Endpoints

Base path: `/api/v1/background`

#### POST /api/v1/background/refresh-market-data
**Description**: Trigger asynchronous market data refresh  
**Authentication**: Required  
**Request Body**:
```json
{
  "symbols": ["AAPL", "MSFT", "GOOGL"],
  "start_date": "2024-01-01",
  "end_date": "2025-01-19",
  "data_types": ["prices", "volumes", "splits"],
  "priority": "high"
}
```
**Response**:
```json
{
  "task_id": "market_refresh_xyz789",
  "status": "queued",
  "message": "Market data refresh initiated",
  "queue": "high_priority",
  "estimated_duration": 300,
  "progress_url": "/api/v1/tasks/market_refresh_xyz789"
}
```

#### POST /api/v1/background/compute-index
**Description**: Trigger index computation in background  
**Authentication**: Required  
**Request Body**:
```json
{
  "start_date": "2024-01-01",
  "end_date": "2025-01-19",
  "strategy_config": {
    "momentum_weight": 0.4,
    "market_cap_weight": 0.3,
    "risk_parity_weight": 0.3
  },
  "force_recompute": false
}
```
**Response**:
```json
{
  "task_id": "index_compute_def456",
  "status": "processing",
  "message": "Index computation started",
  "progress": 0.0,
  "stages": [
    "data_validation",
    "weight_calculation",
    "index_computation",
    "performance_metrics"
  ]
}
```

#### GET /api/v1/background/task/{task_id}
**Description**: Get detailed task status and results  
**Authentication**: Required  
**Response**:
```json
{
  "task_id": "market_refresh_xyz789",
  "name": "market_data_refresh",
  "status": "completed",
  "progress": 1.0,
  "result": {
    "symbols_processed": 25,
    "records_created": 1250,
    "records_updated": 75,
    "errors": [],
    "processing_time": 245.6
  },
  "error": null,
  "traceback": null,
  "created_at": "2025-01-19T12:00:00Z",
  "started_at": "2025-01-19T12:00:15Z",
  "completed_at": "2025-01-19T12:05:00Z",
  "retry_count": 0,
  "max_retries": 3,
  "queue": "high_priority"
}
```

### Diagnostics Endpoints

Base path: `/api/v1/diagnostics`

#### GET /api/v1/diagnostics/system-health
**Description**: Comprehensive system health check  
**Authentication**: Required  
**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-19T14:30:00Z",
  "version": "1.2.0",
  "uptime": 345600,
  "components": {
    "database": {
      "status": "connected",
      "response_time_ms": 12,
      "connections": {
        "active": 5,
        "idle": 15,
        "max": 20
      }
    },
    "redis": {
      "status": "connected",
      "response_time_ms": 2,
      "memory_usage_mb": 45.2,
      "keys_count": 156
    },
    "celery": {
      "status": "running",
      "workers": 3,
      "active_tasks": 2,
      "processed_tasks": 12450
    },
    "external_apis": {
      "twelvedata": {
        "status": "operational",
        "rate_limit": {
          "remaining": 5,
          "reset_in": 45
        },
        "last_error": null
      },
      "marketaux": {
        "status": "operational",
        "rate_limit": {
          "remaining": 85,
          "reset_in": 3600
        },
        "last_error": null
      }
    }
  },
  "system_metrics": {
    "cpu_usage_percent": 45.2,
    "memory_usage_percent": 62.8,
    "disk_usage_percent": 35.4,
    "response_time_ms": 125,
    "requests_per_minute": 180
  }
}
```

#### GET /api/v1/diagnostics/data-quality
**Description**: Data quality assessment and validation  
**Authentication**: Required  
**Query Parameters**:
- `check_type` (optional): prices, news, index (default: all)
- `days_back` (optional): Days to check (default: 30)

**Response**:
```json
{
  "overall_quality_score": 0.95,
  "timestamp": "2025-01-19T14:30:00Z",
  "checks": {
    "price_data": {
      "quality_score": 0.98,
      "total_records": 125000,
      "missing_data_points": 125,
      "duplicate_records": 3,
      "outliers_detected": 15,
      "coverage_percentage": 0.999
    },
    "news_data": {
      "quality_score": 0.92,
      "total_articles": 5600,
      "duplicate_articles": 45,
      "sentiment_coverage": 0.95,
      "entity_extraction_success": 0.98
    },
    "index_data": {
      "quality_score": 0.96,
      "computation_gaps": 2,
      "negative_values": 0,
      "extreme_returns": 5
    }
  },
  "issues": [
    {
      "type": "missing_data",
      "severity": "low",
      "description": "Missing prices for 2 assets on 2025-01-15",
      "affected_assets": ["SYMBOL1", "SYMBOL2"],
      "recommendation": "Backfill missing data",
      "auto_fixable": true
    }
  ],
  "recommendations": [
    "Enable automatic data validation",
    "Increase refresh frequency for critical assets",
    "Review outlier detection thresholds"
  ],
  "last_refresh": "2025-01-19T09:00:00Z",
  "next_check": "2025-01-19T21:00:00Z"
}
```

### Manual Operations Endpoints

Base path: `/api/v1/manual`  
**Note**: These endpoints require admin privileges

#### POST /api/v1/manual/refresh-all
**Description**: Manually trigger complete data refresh  
**Authentication**: Required (Admin)  
**Headers**:
```http
X-Admin-Token: <admin-token>
```
**Request Body**:
```json
{
  "include": ["market_data", "news", "index", "benchmarks"],
  "parallel": true,
  "force": false
}
```
**Response**:
```json
{
  "message": "Full system refresh initiated",
  "task_id": "full_refresh_master_123",
  "components": {
    "market_data": {
      "status": "processing",
      "task_id": "market_data_456"
    },
    "news": {
      "status": "queued",
      "task_id": "news_refresh_789"
    },
    "index_values": {
      "status": "queued",
      "task_id": "index_compute_012"
    },
    "benchmarks": {
      "status": "queued",
      "task_id": "benchmark_345"
    }
  },
  "estimated_completion": "2025-01-19T15:15:00Z"
}
```

#### POST /api/v1/manual/clear-cache
**Description**: Clear Redis cache manually  
**Authentication**: Required (Admin)  
**Request Body**:
```json
{
  "patterns": ["market_data:*", "news:*"],
  "confirm": true
}
```
**Response**:
```json
{
  "message": "Cache cleared successfully",
  "keys_removed": 156,
  "patterns_cleared": ["market_data:*", "news:*"],
  "cache_size_before_mb": 45.2,
  "cache_size_after_mb": 2.1
}
```

#### POST /api/v1/manual/run-migrations
**Description**: Execute database migrations  
**Authentication**: Required (Admin)  
**Request Body**:
```json
{
  "target_version": "latest",
  "dry_run": false
}
```
**Response**:
```json
{
  "message": "Database migrations completed successfully",
  "migrations_executed": [
    {
      "version": "20250119_001",
      "name": "add_composite_indexes",
      "status": "applied",
      "execution_time_ms": 1250
    },
    {
      "version": "20250119_002", 
      "name": "add_performance_indexes",
      "status": "applied",
      "execution_time_ms": 890
    }
  ],
  "total_execution_time_ms": 2140,
  "database_version_before": "20250115_003",
  "database_version_after": "20250119_002"
}
```

## Schemas

### Authentication Schemas

#### RegisterRequest
```python
{
  "email": "string (email format)",
  "password": "string (min 8 chars)",
  "username": "string (optional)"
}
```

#### TokenResponse
```python
{
  "access_token": "string (JWT)",
  "refresh_token": "string (JWT)",
  "token_type": "bearer",
  "expires_in": "integer (seconds)"
}
```

### Strategy Configuration Schema

#### StrategyConfigSchema
```python
{
  "momentum_weight": "float (0-1, default: 0.4)",
  "market_cap_weight": "float (0-1, default: 0.3)", 
  "risk_parity_weight": "float (0-1, default: 0.3)",
  "rebalance_frequency": "string (weekly/monthly/quarterly)",
  "lookback_period": "integer (1-365, default: 30)",
  "daily_drop_threshold": "float (<=0, default: -0.01)",
  "max_daily_return": "float (>=0, default: 0.5)",
  "min_daily_return": "float (<=0, default: -0.5)",
  "min_price_threshold": "float (>=0, default: 1.0)",
  "force_rebalance": "boolean (default: false)"
}
```

### Validation Rules
- All weights must sum to 1.0
- Dates must be ISO 8601 format
- Email addresses validated
- Passwords require complexity

## Error Handling

### Standard Error Response Format
```json
{
  "detail": "Human readable error message",
  "status_code": 400,
  "error_code": "INVALID_REQUEST",
  "timestamp": "2025-01-19T14:30:00Z",
  "request_id": "req_12345",
  "validation_errors": {
    "field_name": ["Field specific error messages"]
  }
}
```

### HTTP Status Codes
- `200 OK`: Success
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters or body
- `401 Unauthorized`: Missing, invalid, or expired authentication token
- `403 Forbidden`: Valid authentication but insufficient permissions
- `404 Not Found`: Requested resource does not exist
- `422 Unprocessable Entity`: Request validation failed
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Unexpected server error
- `503 Service Unavailable`: Service temporarily unavailable

### Custom Error Codes
- `INVALID_TOKEN`: JWT token is invalid or expired
- `RATE_LIMIT_EXCEEDED`: API rate limit reached
- `PROVIDER_ERROR`: External data provider error
- `VALIDATION_FAILED`: Request validation errors
- `INSUFFICIENT_DATA`: Not enough data for calculation
- `CIRCUIT_BREAKER_OPEN`: External service unavailable

## Rate Limiting

### Default Limits
- **Anonymous requests**: 100 requests per minute per IP
- **Authenticated users**: 200 requests per minute per user
- **Admin endpoints**: 50 requests per minute per admin token

### Rate Limit Headers
Response includes:
```http
X-RateLimit-Limit: 200
X-RateLimit-Remaining: 150
X-RateLimit-Reset: 1642687200
X-RateLimit-Window: 60
```

### Rate Limit Response
When exceeded:
```json
{
  "detail": "Rate limit exceeded",
  "status_code": 429,
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 60,
  "limit": 200,
  "window": 60
}
```

## Integration Notes

### Provider Integration
The API integrates with external data providers using a clean provider pattern:

#### TwelveData (Market Data)
- **Purpose**: Historical prices, real-time quotes, exchange rates
- **Rate Limits**: 8 credits/minute (free tier)
- **Caching**: 1 hour for historical data, 1 minute for quotes
- **Circuit Breaker**: Opens after 5 consecutive failures

#### Marketaux (News & Sentiment) 
- **Purpose**: Financial news, sentiment analysis, entity extraction
- **Rate Limits**: Configurable per plan
- **Caching**: 15 minutes for articles, 1 hour for sentiment
- **Features**: 5,000+ sources, 30+ languages, real-time updates

### Caching Strategy
Redis-based caching with automatic invalidation:
- **Market Data**: TTL based on data freshness requirements
- **News Articles**: 15-minute TTL with refresh-ahead pattern
- **Performance Metrics**: 1-hour TTL with background computation
- **User Sessions**: 30-minute TTL with sliding expiration

### Background Processing
Celery with Redis broker for async operations:
- **Market Data Refresh**: Scheduled daily at market close
- **Index Computation**: Triggered after data refresh
- **News Collection**: Continuous with 15-minute intervals
- **Performance Calculations**: On-demand and scheduled

### Database Optimization
- **Composite Indexes**: Optimized for common query patterns
- **Partitioning**: Time-based partitioning for large tables
- **Connection Pooling**: Optimized pool sizes for workload
- **Query Optimization**: Materialized views for complex analytics

### Security Features
- **JWT Authentication**: RS256 algorithm with key rotation
- **Password Security**: bcrypt hashing with cost factor 12
- **Rate Limiting**: Distributed rate limiting with Redis
- **CORS Protection**: Configurable allowed origins
- **SQL Injection Prevention**: Parameterized queries with SQLAlchemy
- **Input Validation**: Comprehensive Pydantic validation

### Monitoring & Observability
- **Health Checks**: Multi-level health monitoring
- **Metrics Collection**: Custom metrics for business KPIs
- **Error Tracking**: Structured logging with correlation IDs
- **Performance Monitoring**: Response time and throughput tracking
- **Alert System**: Configurable alerts for critical issues

### Deployment Considerations
- **Environment Variables**: Comprehensive configuration management
- **Docker Support**: Multi-stage builds with optimization
- **Database Migrations**: Automated schema management
- **Zero-Downtime Deployment**: Blue-green deployment support
- **Scaling**: Horizontal scaling with load balancing

This API reference provides comprehensive documentation for integrating with the Waardhaven AutoIndex system. For additional technical details, refer to the implementation guides and deployment documentation.