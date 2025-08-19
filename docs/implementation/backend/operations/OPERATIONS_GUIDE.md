# Waardhaven AutoIndex Operations Guide

## Table of Contents
- [Overview](#overview)
- [Database Operations](#database-operations)
- [Scripts & Utilities](#scripts--utilities)
- [Deployment Operations](#deployment-operations)
- [System Administration](#system-administration)
- [Background Tasks](#background-tasks)
- [Monitoring & Diagnostics](#monitoring--diagnostics)
- [Backup & Recovery](#backup--recovery)
- [Performance Tuning](#performance-tuning)
- [Troubleshooting](#troubleshooting)

## Overview

This guide provides comprehensive operational procedures for managing the Waardhaven AutoIndex system in production and development environments. It covers database management, deployment operations, system monitoring, and maintenance tasks.

### System Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   API Gateway   │
│   (Next.js)     │     │   (FastAPI)     │
└─────────────────┘     └─────────────────┘
                              │
                    ┌─────────┼─────────┐
                    │         │         │
                    ▼         ▼         ▼
          ┌─────────────┐ ┌─────────┐ ┌──────────────┐
          │ PostgreSQL  │ │  Redis  │ │    Celery    │
          │  Database   │ │  Cache  │ │   Workers    │
          └─────────────┘ └─────────┘ └──────────────┘
```

### Key Components
- **Database**: PostgreSQL with TimescaleDB for time-series data
- **Cache**: Redis for session storage and API response caching  
- **Queue**: Celery with Redis broker for background tasks
- **API**: FastAPI with SQLAlchemy ORM and Pydantic validation
- **Frontend**: Next.js with TypeScript and Tailwind CSS

## Database Operations

### Database Architecture

#### Core Tables
- **users**: Authentication and user management
- **assets**: Financial instruments (stocks, ETFs, commodities)
- **prices**: Historical price data with composite indexing
- **index_values**: Calculated portfolio index values (base 100)
- **allocations**: Portfolio asset weights over time
- **strategy_configs**: Dynamic investment strategy parameters
- **news_articles**: Financial news with full-text search
- **news_sentiment**: AI-driven sentiment analysis results

#### Performance Tables
- **risk_metrics**: Calculated performance metrics
- **market_cap_data**: Market capitalization and trading volumes
- **insider_transactions**: Insider trading tracking
- **institutional_holdings**: 13F filings and institutional data

### Database Initialization

#### Initial Setup
```bash
# Navigate to API directory
cd apps/api

# Initialize database schema
python -m app.db_init

# Seed default assets
python -m app.seed_assets

# Create admin user (optional)
python -m app.create_admin_user
```

#### Schema Creation Script (`db_init.py`)
The initialization script performs these operations:
- Creates all tables using SQLAlchemy metadata
- Establishes foreign key relationships
- Creates composite indexes for performance
- Sets up default strategy configuration

**Default Strategy Configuration**:
```python
{
    "momentum_weight": 0.4,        # 40% momentum strategy
    "market_cap_weight": 0.3,      # 30% market cap weighting  
    "risk_parity_weight": 0.3,     # 30% risk parity
    "min_price_threshold": 1.0,    # $1 minimum price
    "max_daily_return": 0.5,       # 50% daily return cap
    "min_daily_return": -0.5,      # -50% daily return floor
    "rebalance_frequency": "weekly",
    "daily_drop_threshold": -0.01  # -1% drop alert
}
```

### Database Migrations

#### Manual Migrations
```bash
# Run all pending migrations
python -m app.migrations.run_all

# Run specific migration
python -m app.migrations.add_news_tables

# Create new migration
python -m app.migrations.create_migration "description"
```

#### Migration Safety Features
- **Backup Creation**: Automatic backup before migrations
- **Transaction Wrapping**: All migrations in transactions with rollback
- **Validation**: Post-migration data integrity checks
- **Idempotent**: Safe to run multiple times

### Database Maintenance

#### Daily Operations
```bash
# Update table statistics
python -m app.utils.analyze_tables

# Check data quality
python -m app.diagnostics.data_quality_check

# Backup database
pg_dump $DATABASE_URL > backups/$(date +%Y%m%d)_backup.sql
```

#### Performance Optimization
```sql
-- Composite indexes for common queries
CREATE INDEX CONCURRENTLY idx_price_asset_date ON prices(asset_id, date);
CREATE INDEX CONCURRENTLY idx_allocation_date ON allocations(date);
CREATE INDEX CONCURRENTLY idx_news_published ON news_articles(published_at DESC);

-- Partial indexes for active data
CREATE INDEX CONCURRENTLY idx_active_assets ON assets(symbol) 
WHERE is_active = true;
```

#### Data Cleanup
```bash
# Remove old cache entries
python -m app.utils.cleanup_cache --days 7

# Archive old news articles  
python -m app.utils.archive_old_news --days 90

# Cleanup failed tasks
python -m app.utils.cleanup_failed_tasks --days 3
```

### Connection Management

#### Connection Pool Configuration
```python
# Database connection settings
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=20,                    # Base connections
    max_overflow=30,                 # Additional connections
    pool_pre_ping=True,              # Validate connections
    pool_recycle=3600,               # Recycle after 1 hour
    pool_timeout=30,                 # Connection timeout
)
```

#### Connection Monitoring
```bash
# Check active connections
SELECT count(*) as active_connections 
FROM pg_stat_activity 
WHERE state = 'active';

# Monitor connection pool status
python -m app.diagnostics.connection_pool_status
```

## Scripts & Utilities

### Core Initialization Scripts

#### `db_init.py` - Database Initialization
**Location**: `apps/api/app/db_init.py`

**Purpose**:
- Creates all database tables from SQLAlchemy models
- Establishes default strategy configuration
- Ensures referential integrity with foreign keys

**Usage**:
```bash
# Command line
python -m app.db_init

# Programmatic
from app.db_init import main
main()

# Docker startup (automatic)
./scripts/startup.sh
```

**Safety Features**:
- Idempotent operations (safe to run multiple times)
- Proper exception handling with database rollback
- Comprehensive logging for audit trail

#### `seed_assets.py` - Asset Population
**Location**: `apps/api/app/seed_assets.py`

**Purpose**:
- Populates assets table with S&P 500 stocks
- Adds ETF and benchmark assets
- Creates sector classifications

**Asset Categories**:
```python
# S&P 500 stocks (500 assets)
LARGE_CAP_STOCKS = ["AAPL", "MSFT", "GOOGL", "AMZN", ...]

# ETFs and benchmarks
BENCHMARK_ETFS = ["SPY", "QQQ", "IWM", "VTI", "VXUS"]

# Commodities
COMMODITIES = ["GLD", "SLV", "USO", "DBA"]
```

#### `tasks_refresh.py` - Data Refresh Operations
**Location**: `apps/api/app/tasks/refresh.py`

**Purpose**:
- Orchestrates market data refresh from TwelveData
- Manages news collection from Marketaux
- Handles index computation and performance metrics

**Refresh Types**:
- **Smart Refresh**: Only missing/stale data
- **Full Refresh**: Complete data reload
- **Targeted Refresh**: Specific symbols or date ranges

### Database Management Scripts

#### Migration Scripts
```bash
# apps/api/app/migrations/
├── add_news_tables.py          # News and sentiment tables
├── add_composite_indexes.py    # Performance indexes
├── add_insider_trading.py      # Insider trading tables
├── add_performance_tables.py   # Risk metrics tables
└── run_all.py                  # Migration orchestrator
```

#### Utility Scripts
```bash
# apps/api/app/utils/
├── run_migrations.py           # Database migration runner
├── cleanup_old_data.py         # Data archival and cleanup
├── backup_database.py          # Database backup utilities
├── restore_database.py         # Database restoration tools
├── analyze_performance.py      # Query performance analysis
└── validate_data_integrity.py  # Data consistency checks
```

### Operational Scripts

#### System Diagnostics
```bash
# Complete system health check
python -m app.diagnostics.full_system_check

# Database connectivity test
python -m app.diagnostics.test_db_connection

# External API health check
python -m app.diagnostics.test_external_apis

# Cache system validation
python -m app.diagnostics.test_redis_connection
```

#### Data Quality Scripts
```bash
# Comprehensive data quality assessment
python -m app.quality.assess_data_quality

# Find and fix missing price data
python -m app.quality.fix_missing_prices

# Detect and handle outliers
python -m app.quality.detect_outliers

# Validate index calculations
python -m app.quality.validate_index_calculations
```

### Backup and Recovery Scripts

#### Automated Backup
```bash
#!/bin/bash
# scripts/backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Database backup
pg_dump $DATABASE_URL > "$BACKUP_DIR/db_$DATE.sql"

# Configuration backup
cp apps/api/.env "$BACKUP_DIR/config_$DATE.env"

# Upload to cloud storage (optional)
aws s3 cp "$BACKUP_DIR/db_$DATE.sql" s3://waardhaven-backups/
```

#### Recovery Scripts
```bash
#!/bin/bash
# scripts/restore.sh
if [ -z "$1" ]; then
  echo "Usage: ./restore.sh <backup_file>"
  exit 1
fi

# Stop services
docker-compose down

# Restore database
psql $DATABASE_URL < "$1"

# Restart services
docker-compose up -d
```

## Deployment Operations

### Production Deployment on Render.com

#### Service Configuration
```yaml
# render.yaml
services:
  - type: web
    name: waardhaven-api
    env: docker
    plan: starter
    dockerfilePath: ./Dockerfile
    rootDir: apps/api
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: waardhaven-db
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: REDIS_URL
        fromService:
          type: redis
          name: waardhaven-redis
```

#### Environment Configuration
```bash
# Production environment variables
SECRET_KEY=<generated-32-char-key>
ADMIN_TOKEN=<secure-admin-token>
TWELVEDATA_API_KEY=<api-key>
MARKETAUX_API_KEY=<api-key>
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://default:pass@host:6379
FRONTEND_URL=https://waardhaven-web.onrender.com
ENABLE_CACHE=true
ENABLE_BACKGROUND_TASKS=true
LOG_LEVEL=INFO
```

#### Deployment Process
```bash
# 1. Pre-deployment checks
python -m app.diagnostics.pre_deployment_check

# 2. Database migrations
python -m app.migrations.run_all

# 3. Data validation
python -m app.diagnostics.validate_deployment

# 4. Cache warming
python -m app.utils.warm_cache

# 5. Health check verification
curl https://api.example.com/health
```

### Docker Deployment

#### Production Dockerfile
```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY app ./app
COPY scripts ./scripts
RUN chmod +x scripts/*.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
CMD ["./scripts/startup.sh"]
```

#### Startup Script
```bash
#!/bin/bash
# scripts/startup.sh
set -e

echo "Starting Waardhaven AutoIndex API..."

# Wait for database
echo "Waiting for database..."
while ! pg_isready -h "${DATABASE_HOST:-db}" -p "${DATABASE_PORT:-5432}"; do
  sleep 2
done

# Run migrations
echo "Running database migrations..."
python -m app.migrations.run_all

# Initialize database if needed
echo "Initializing database..."
python -m app.db_init

# Start application
echo "Starting FastAPI server..."
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers "${WORKERS:-4}" \
  --access-log \
  --log-config app/core/logging_config.json
```

### Local Development Setup

#### Development Environment
```bash
# Clone repository
git clone https://github.com/yourusername/waardhaven-autoindex.git
cd waardhaven-autoindex

# Set up Python environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
cd apps/api
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python -m app.db_init
python -m app.seed_assets

# Start development server
uvicorn app.main:app --reload --port 8000
```

#### Docker Compose Development
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: waardhaven_dev
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev123
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  api:
    build:
      context: ./apps/api
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://dev:dev123@db:5432/waardhaven_dev
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./apps/api:/app
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

## System Administration

### User Management

#### Admin User Creation
```python
# Create admin user programmatically
from app.models.user import User
from app.core.database import SessionLocal
from app.utils.security import get_password_hash

def create_admin_user(email: str, password: str):
    db = SessionLocal()
    try:
        admin_user = User(
            email=email,
            password_hash=get_password_hash(password),
            is_admin=True
        )
        db.add(admin_user)
        db.commit()
        print(f"Admin user created: {email}")
    finally:
        db.close()

# Usage
create_admin_user("admin@example.com", "secure-password")
```

#### User Access Management
```bash
# List all users
python -m app.admin.list_users

# Deactivate user
python -m app.admin.deactivate_user --email user@example.com

# Reset user password
python -m app.admin.reset_password --email user@example.com

# Grant admin privileges
python -m app.admin.grant_admin --email user@example.com
```

### Configuration Management

#### Strategy Configuration Updates
```python
# Update strategy via API
curl -X POST /api/v1/strategy/update \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "momentum_weight": 0.5,
    "market_cap_weight": 0.3,
    "risk_parity_weight": 0.2,
    "rebalance_frequency": "monthly"
  }'

# Programmatic update
from app.services.strategy import update_strategy_config
update_strategy_config(user_id=None, config=new_config)
```

#### System Settings
```bash
# Enable/disable features
export ENABLE_BACKGROUND_TASKS=true
export ENABLE_CACHE=true
export SKIP_STARTUP_REFRESH=false

# Adjust rate limits
export RATE_LIMIT_CALLS=200
export RATE_LIMIT_PERIOD=60

# Logging configuration
export LOG_LEVEL=INFO
export LOG_FORMAT=json
```

### Security Operations

#### JWT Token Management
```python
# Generate new secret key
import secrets
new_secret = secrets.token_urlsafe(32)
print(f"New SECRET_KEY: {new_secret}")

# Invalidate all tokens (change secret key)
# Update SECRET_KEY in environment and restart
```

#### SSL/TLS Configuration
```nginx
# Nginx configuration for SSL termination
server {
    listen 443 ssl http2;
    server_name api.example.com;
    
    ssl_certificate /etc/ssl/certs/api.example.com.crt;
    ssl_certificate_key /etc/ssl/private/api.example.com.key;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Background Tasks

### Celery Configuration

#### Worker Setup
```python
# app/core/celery_app.py
from celery import Celery

celery_app = Celery(
    "waardhaven",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["app.tasks.refresh", "app.tasks.calculations"]
)

# Task routing
celery_app.conf.task_routes = {
    "app.tasks.refresh.market_data": {"queue": "data_refresh"},
    "app.tasks.calculations.compute_index": {"queue": "calculations"},
    "app.tasks.news.collect_news": {"queue": "news"},
}
```

#### Task Definitions
```python
# Market data refresh task
@celery_app.task(bind=True, max_retries=3)
def refresh_market_data(self, symbols=None, start_date=None):
    try:
        from app.services.refresh import RefreshService
        service = RefreshService()
        return service.refresh_market_data(symbols, start_date)
    except Exception as exc:
        # Exponential backoff retry
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

# Index computation task
@celery_app.task(bind=True)
def compute_index_values(self, start_date=None, end_date=None):
    from app.services.index import IndexService
    service = IndexService()
    return service.compute_values(start_date, end_date)
```

#### Worker Management
```bash
# Start worker processes
celery -A app.core.celery_app worker --loglevel=info --concurrency=4

# Start beat scheduler
celery -A app.core.celery_app beat --loglevel=info

# Monitor with Flower
celery -A app.core.celery_app flower --port=5555

# Scale workers
celery -A app.core.celery_app control autoscale 10 3
```

### Task Monitoring

#### Task Status Tracking
```python
# Check task status
from app.core.celery_app import celery_app

task = refresh_market_data.delay(symbols=["AAPL", "MSFT"])
print(f"Task ID: {task.id}")
print(f"Status: {task.status}")
print(f"Result: {task.result}")

# List active tasks
active_tasks = celery_app.control.inspect().active()
for worker, tasks in active_tasks.items():
    print(f"Worker {worker}: {len(tasks)} active tasks")
```

#### Scheduled Tasks
```python
# Periodic task configuration
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'refresh-market-data-daily': {
        'task': 'app.tasks.refresh.market_data',
        'schedule': crontab(hour=18, minute=0),  # 6 PM daily
    },
    'compute-index-values': {
        'task': 'app.tasks.calculations.compute_index',
        'schedule': crontab(hour=19, minute=0),  # 7 PM daily
    },
    'collect-news': {
        'task': 'app.tasks.news.collect_news',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
}
```

## Monitoring & Diagnostics

### System Health Monitoring

#### Health Check Endpoints
```python
# Basic health check
GET /health
{
  "status": "healthy",
  "timestamp": "2025-01-19T14:30:00Z"
}

# Comprehensive system health
GET /api/v1/diagnostics/system-health
{
  "status": "healthy",
  "components": {
    "database": "connected",
    "redis": "connected", 
    "celery": "running",
    "external_apis": {
      "twelvedata": "operational",
      "marketaux": "operational"
    }
  },
  "metrics": {
    "cpu_usage": 45.2,
    "memory_usage": 62.8,
    "response_time_ms": 125
  }
}
```

#### Data Quality Monitoring
```python
# Data quality assessment
GET /api/v1/diagnostics/data-quality
{
  "quality_score": 0.95,
  "issues": [
    {
      "type": "missing_data",
      "severity": "low",
      "description": "Missing prices for 2 assets",
      "affected_assets": ["SYMBOL1", "SYMBOL2"],
      "auto_fixable": true
    }
  ],
  "data_coverage": {
    "assets": 495,
    "dates": 250,
    "completeness": 0.98
  }
}
```

### Performance Monitoring

#### Application Metrics
```python
# Custom metrics collection
import time
from functools import wraps

def track_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        
        # Log performance metric
        logger.info(f"{func.__name__} completed in {duration:.2f}s")
        return result
    return wrapper

# Database query performance
@track_performance
def get_price_history(symbol, days):
    return db.query(Price).filter(
        Price.asset.has(symbol=symbol),
        Price.date >= (datetime.now() - timedelta(days=days))
    ).all()
```

#### Resource Monitoring
```bash
# System resource usage
python -m app.diagnostics.resource_usage

# Database connection monitoring
python -m app.diagnostics.connection_monitoring

# Cache performance metrics
python -m app.diagnostics.cache_metrics

# API response time analysis
python -m app.diagnostics.response_time_analysis
```

### Logging Configuration

#### Structured Logging
```json
{
  "version": 1,
  "disable_existing_loggers": false,
  "formatters": {
    "default": {
      "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    },
    "json": {
      "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
      "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
    }
  },
  "handlers": {
    "console": {
      "class": "logging.StreamHandler",
      "formatter": "json",
      "stream": "ext://sys.stdout"
    },
    "file": {
      "class": "logging.handlers.RotatingFileHandler",
      "formatter": "json",
      "filename": "logs/app.log",
      "maxBytes": 10485760,
      "backupCount": 5
    }
  },
  "loggers": {
    "app": {
      "level": "INFO",
      "handlers": ["console", "file"],
      "propagate": false
    },
    "sqlalchemy": {
      "level": "WARN",
      "handlers": ["console"],
      "propagate": false
    }
  }
}
```

### Alert System

#### Alert Configuration
```python
# Alert thresholds
ALERT_THRESHOLDS = {
    "response_time_ms": 1000,
    "error_rate_percent": 5,
    "database_connections": 18,
    "memory_usage_percent": 85,
    "data_quality_score": 0.9
}

# Alert handlers
async def send_alert(alert_type: str, message: str, severity: str):
    # Send to monitoring service
    await monitoring_service.send_alert({
        "type": alert_type,
        "message": message,
        "severity": severity,
        "timestamp": datetime.utcnow(),
        "service": "waardhaven-api"
    })
```

## Backup & Recovery

### Database Backup Strategy

#### Automated Backups
```bash
#!/bin/bash
# Automated backup script with retention
BACKUP_DIR="/backups/database"
RETENTION_DAYS=30

# Create backup with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/waardhaven_$TIMESTAMP.sql"

# Perform backup
pg_dump $DATABASE_URL | gzip > "$BACKUP_FILE.gz"

# Verify backup integrity
gunzip -t "$BACKUP_FILE.gz"
if [ $? -eq 0 ]; then
    echo "Backup created successfully: $BACKUP_FILE.gz"
else
    echo "Backup verification failed!"
    exit 1
fi

# Clean old backups
find $BACKUP_DIR -name "*.gz" -mtime +$RETENTION_DAYS -delete

# Upload to cloud storage
aws s3 cp "$BACKUP_FILE.gz" s3://waardhaven-backups/database/
```

#### Point-in-Time Recovery
```bash
# Enable WAL archiving for PITR
# In postgresql.conf:
# wal_level = replica
# archive_mode = on
# archive_command = 'cp %p /backups/wal/%f'

# Create base backup
pg_basebackup -D /backups/base -Ft -z -P

# Recovery to specific point in time
# In recovery.conf:
# restore_command = 'cp /backups/wal/%f %p'
# recovery_target_time = '2025-01-19 14:30:00'
```

### Application State Backup

#### Configuration Backup
```bash
# Backup configuration files
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
  apps/api/.env \
  apps/web/.env \
  docker-compose.yml \
  render.yaml

# Backup uploaded files (if any)
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz \
  uploads/
```

#### Cache State Backup
```bash
# Redis backup
redis-cli SAVE
cp /var/lib/redis/dump.rdb backups/redis_$(date +%Y%m%d).rdb

# Or use BGSAVE for non-blocking backup
redis-cli BGSAVE
```

### Disaster Recovery Procedures

#### Complete System Recovery
```bash
#!/bin/bash
# Disaster recovery script
set -e

echo "Starting disaster recovery process..."

# 1. Restore database
echo "Restoring database..."
gunzip -c backups/database/latest.sql.gz | psql $DATABASE_URL

# 2. Restore configuration
echo "Restoring configuration..."
tar -xzf backups/config/latest.tar.gz

# 3. Restore cache
echo "Restoring Redis cache..."
cp backups/redis/latest.rdb /var/lib/redis/dump.rdb
systemctl restart redis

# 4. Validate system
echo "Validating system health..."
python -m app.diagnostics.full_system_check

echo "Disaster recovery completed successfully!"
```

#### Recovery Time Objectives (RTO)
- **Database Recovery**: 30 minutes maximum
- **Application Restart**: 5 minutes maximum
- **Full System Recovery**: 1 hour maximum
- **Data Loss (RPO)**: 1 hour maximum

## Performance Tuning

### Database Performance

#### Index Optimization
```sql
-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM prices 
WHERE asset_id = 1 AND date >= '2024-01-01';

-- Create optimal indexes
CREATE INDEX CONCURRENTLY idx_price_asset_date_covering 
ON prices(asset_id, date) INCLUDE (close, volume);

-- Monitor index usage
SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes 
ORDER BY idx_tup_read DESC;
```

#### Query Optimization
```python
# Efficient batch loading
def load_price_data_batch(asset_ids: List[int], start_date: date):
    return db.query(Price).options(
        joinedload(Price.asset)
    ).filter(
        Price.asset_id.in_(asset_ids),
        Price.date >= start_date
    ).order_by(Price.asset_id, Price.date).all()

# Pagination for large datasets
def get_paginated_prices(offset: int = 0, limit: int = 100):
    return db.query(Price).offset(offset).limit(limit).all()
```

#### Connection Pool Tuning
```python
# Optimized connection pool
engine = create_engine(
    DATABASE_URL,
    pool_size=20,                    # Base connections
    max_overflow=30,                 # Additional connections
    pool_pre_ping=True,              # Validate connections
    pool_recycle=3600,               # Recycle after 1 hour
    pool_timeout=30,                 # Connection timeout
    echo_pool=True,                  # Debug connection pool
)
```

### Application Performance

#### Caching Strategy
```python
# Multi-level caching
import redis
from functools import wraps

redis_client = redis.Redis.from_url(os.getenv("REDIS_URL"))

def cache_result(ttl: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try cache first
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator

# Usage
@cache_result(ttl=600)  # 10-minute cache
async def get_portfolio_performance(user_id: int):
    # Expensive calculation here
    pass
```

#### Background Task Optimization
```python
# Optimized Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    result_expires=3600,
    task_compression='gzip',
    worker_prefetch_multiplier=4,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_routes={
        'app.tasks.priority': {'queue': 'priority'},
        'app.tasks.bulk': {'queue': 'bulk'},
    }
)
```

### System Resource Optimization

#### Memory Management
```python
# Memory-efficient data processing
import gc
from typing import Iterator

def process_large_dataset(batch_size: int = 1000) -> Iterator:
    """Process large datasets in batches to manage memory"""
    offset = 0
    while True:
        batch = db.query(Price).offset(offset).limit(batch_size).all()
        if not batch:
            break
        
        yield batch
        
        # Explicit garbage collection
        gc.collect()
        offset += batch_size
```

#### CPU Optimization
```python
# Use multiprocessing for CPU-intensive tasks
from multiprocessing import Pool
import numpy as np

def calculate_performance_metrics_parallel(asset_data):
    """Calculate metrics using multiple CPU cores"""
    with Pool() as pool:
        results = pool.map(calculate_single_asset_metrics, asset_data)
    return results

# Vectorized operations with NumPy
def calculate_returns_vectorized(prices: np.array) -> np.array:
    """Use NumPy for fast mathematical operations"""
    return np.diff(prices) / prices[:-1]
```

## Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Symptom: "connection pool exhausted"
# Solution: Check connection pool settings
python -c "
from app.core.database import engine
print(f'Pool size: {engine.pool.size()}')
print(f'Checked out: {engine.pool.checkedout()}')
"

# Fix: Increase pool size or find connection leaks
# In database.py, increase pool_size and max_overflow
```

#### Memory Issues
```bash
# Symptom: Out of memory errors
# Check memory usage
free -h
ps aux --sort=-%mem | head -20

# Solution: Optimize queries and enable pagination
# Monitor memory usage in application
import psutil
print(f"Memory usage: {psutil.virtual_memory().percent}%")
```

#### Performance Issues
```sql
-- Identify slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;

-- Check index usage
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE tablename = 'prices'
ORDER BY n_distinct DESC;
```

### Error Resolution

#### API Error Handling
```python
# Custom exception handling
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

async def custom_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": str(uuid.uuid4())
        }
    )

# Rate limit handling
@app.exception_handler(429)
async def rate_limit_handler(request: Request, exc):
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded",
            "retry_after": 60
        }
    )
```

#### Background Task Failures
```python
# Task retry with exponential backoff
@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def resilient_task(self, data):
    try:
        # Task logic here
        return process_data(data)
    except TemporaryError as exc:
        # Retry with exponential backoff
        countdown = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=countdown)
    except PermanentError:
        # Don't retry permanent errors
        logger.error(f"Permanent error in task: {exc}")
        raise
```

### Debugging Tools

#### SQL Query Analysis
```python
# Enable SQLAlchemy query logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Query profiling
from sqlalchemy import text

def profile_query(query_str: str):
    with engine.begin() as conn:
        # Get query plan
        explain_result = conn.execute(text(f"EXPLAIN ANALYZE {query_str}"))
        for row in explain_result:
            print(row)
```

#### Performance Profiling
```python
import cProfile
import pstats

def profile_function(func, *args, **kwargs):
    """Profile a function's performance"""
    profiler = cProfile.Profile()
    profiler.enable()
    
    result = func(*args, **kwargs)
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative').print_stats(10)
    
    return result
```

#### Health Check Debugging
```bash
# Complete system diagnostic
python -m app.diagnostics.debug_system_health

# Test external API connectivity
python -m app.diagnostics.test_external_apis

# Validate data integrity
python -m app.diagnostics.validate_data_integrity

# Check cache performance
python -m app.diagnostics.cache_performance_test
```

This operations guide provides comprehensive procedures for managing the Waardhaven AutoIndex system effectively in production environments. Regular monitoring and proactive maintenance using these procedures will ensure optimal system performance and reliability.