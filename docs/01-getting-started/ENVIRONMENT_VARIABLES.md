# Environment Variables Documentation

## Overview
Complete reference for all environment variables used across the Waardhaven AutoIndex platform.

## Backend Environment Variables (`apps/api/.env`)

### Database Configuration
```env
# PostgreSQL Database URL
DATABASE_URL=postgresql://user:password@localhost:5432/waardhaven_db
# Format: postgresql://[user]:[password]@[host]:[port]/[database]
```

### Authentication & Security
```env
# JWT Secret Key for token signing (generate with: openssl rand -hex 32)
SECRET_KEY=your-secret-key-here

# Admin access token for protected endpoints
ADMIN_TOKEN=your-admin-token-here
```

### External API Keys
```env
# TwelveData API key for market data
TWELVEDATA_API_KEY=your-twelvedata-api-key

# MarketAux API key for news data (optional)
MARKETAUX_API_KEY=your-marketaux-api-key
```

### CORS Configuration
```env
# Frontend URL for CORS
FRONTEND_URL=http://localhost:3000
# In production: https://your-frontend-domain.com
```

### Application Settings
```env
# Skip automatic data refresh on startup
SKIP_STARTUP_REFRESH=true

# Debug mode (enables detailed logging)
DEBUG=false
DEBUG_MODE=false  # Alternative debug flag used in startup.sh

# Port for API server
PORT=8000

# Startup script configuration
MAX_DB_RETRIES=60        # Maximum database connection retries
REFRESH_TIMEOUT=120      # Timeout for refresh operation in seconds
DB_INIT_DELAYED=false    # Delay database initialization (set by startup.sh)

# Production environment detection
RENDER=true              # Automatically set by Render.com in production
PRODUCTION=false         # Force production mode
```

### Strategy Configuration
```env
# Default investment strategy parameters
DAILY_DROP_THRESHOLD=-0.01
ASSET_DEFAULT_START=2018-01-01
SP500_TICKER=^GSPC
```

### Redis Cache Configuration
```env
# Redis connection URL
REDIS_URL=redis://localhost:6379/0

# Cache TTL settings (in seconds)
CACHE_TTL_SECONDS=300      # Default cache TTL (5 minutes)
CACHE_TTL_LONG_SECONDS=3600 # Long cache TTL (1 hour)
```

### Celery Background Tasks
```env
# Celery is fully implemented and operational
# Configuration is handled in app/core/celery_app.py
CELERY_BROKER_URL=redis://localhost:6379/0      # Redis broker for task queue
CELERY_RESULT_BACKEND=redis://localhost:6379/0   # Redis backend for results

# Note: These variables are read directly in celery_app.py
# The broker and backend default to REDIS_URL if not specified
```

### Provider Settings
```env
# Rate limiting (configured in config.py)
TWELVEDATA_RATE_LIMIT=8  # requests per minute (free tier)
MARKETAUX_RATE_LIMIT=100  # requests per minute (default in config.py)

# Cache and refresh settings
ENABLE_MARKET_DATA_CACHE=true
ENABLE_NEWS_CACHE=true
REFRESH_MODE=auto  # auto, full, minimal, cached
NEWS_REFRESH_INTERVAL=900  # 15 minutes
```

## Frontend Environment Variables (`apps/web/.env`)

> **⚠️ IMPORTANT NOTE**: Currently, the frontend only actively uses `NEXT_PUBLIC_API_URL`. The other environment variables listed below are included as best practices for environment variable management and may be utilized in future implementations.

### API Configuration (ACTIVELY USED)
```env
# Backend API URL - THIS IS THE ONLY ENV VAR CURRENTLY USED BY THE FRONTEND
NEXT_PUBLIC_API_URL=http://localhost:8000
# In production: https://your-api-domain.com
```

### Application Settings (BEST PRACTICES - NOT CURRENTLY USED)
```env
# Port for frontend server
PORT=3000

# Node environment
NODE_ENV=development
# In production: NODE_ENV=production

# The following are documented for future use and best practices:
# NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-oauth-client-id
# NEXT_PUBLIC_ENABLE_ANALYTICS=false
# NEXT_PUBLIC_SENTRY_DSN=your-sentry-dsn
# NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8000
```

## Deployment Environment Variables (Render.com)

### Backend Service (`render.yaml`)
```yaml
envVars:
  - key: PORT
    value: "10000"
  - key: SECRET_KEY
    sync: false  # Set in Render dashboard
  - key: DATABASE_URL
    fromDatabase:
      name: waardhaven-db
      property: connectionString
  - key: ADMIN_TOKEN
    sync: false  # Set in Render dashboard
  - key: TWELVEDATA_API_KEY
    sync: false  # Set in Render dashboard
  - key: DAILY_DROP_THRESHOLD
    value: "-0.01"
  - key: ASSET_DEFAULT_START
    value: "2018-01-01"
  - key: SP500_TICKER
    value: "^GSPC"
  - key: FRONTEND_URL
    sync: false  # Set in Render dashboard
```

### Frontend Service (`render.yaml`)
```yaml
envVars:
  - key: PORT
    value: "10000"
  - key: NEXT_PUBLIC_API_URL
    sync: false  # Set in Render dashboard
```

## Example `.env` Files

### Backend `.env.example`
```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/waardhaven_db

# Security
SECRET_KEY=your-secret-key-generate-with-openssl-rand-hex-32
ADMIN_TOKEN=your-admin-token-here

# External APIs
TWELVEDATA_API_KEY=demo
MARKETAUX_API_KEY=

# CORS
FRONTEND_URL=http://localhost:3000

# Application
SKIP_STARTUP_REFRESH=true
DEBUG=false
PORT=8000

# Strategy
DAILY_DROP_THRESHOLD=-0.01
ASSET_DEFAULT_START=2018-01-01
SP500_TICKER=^GSPC

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Frontend `.env.example`
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
PORT=3000
NODE_ENV=development
```

## Environment Variable Priority

1. **System environment variables** (highest priority)
2. **`.env.local`** file (for local overrides)
3. **`.env`** file (project defaults)
4. **Default values in code** (fallback)

## Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use `.env.example`** files for documentation
3. **Generate strong secrets**:
   ```bash
   # Generate SECRET_KEY
   openssl rand -hex 32
   
   # Generate ADMIN_TOKEN
   openssl rand -base64 32
   ```
4. **Use different values** for development and production
5. **Rotate secrets regularly** in production
6. **Use secret management services** (e.g., AWS Secrets Manager, HashiCorp Vault)

## Validation

The application validates required environment variables on startup:
- Backend: `apps/api/app/core/config.py`
- Frontend: `apps/web/app/utils/env-validator.ts`

Missing required variables will cause the application to fail with descriptive error messages.

## Docker Environment

When using Docker, environment variables can be:
1. Set in `docker-compose.yml`
2. Passed via `--env-file` flag
3. Set in Dockerfile with `ENV` instruction

Example `docker-compose.yml`:
```yaml
services:
  api:
    env_file:
      - ./apps/api/.env
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/waardhaven
  
  web:
    env_file:
      - ./apps/web/.env
    environment:
      - NEXT_PUBLIC_API_URL=http://api:8000
```

## Troubleshooting

### Common Issues

1. **"Environment variable X is not set"**
   - Check `.env` file exists and is in correct location
   - Verify variable name spelling
   - Restart application after adding variables

2. **"Invalid DATABASE_URL"**
   - Verify PostgreSQL is running
   - Check connection string format
   - Test with `psql` command

3. **"CORS error"**
   - Ensure `FRONTEND_URL` matches actual frontend URL
   - Include protocol (http:// or https://)
   - Check for trailing slashes

4. **"API key invalid"**
   - Verify API key with provider
   - Check for extra spaces or quotes
   - Ensure key has required permissions

## References

- [Next.js Environment Variables](https://nextjs.org/docs/basic-features/environment-variables)
- [FastAPI Settings](https://fastapi.tiangolo.com/advanced/settings/)
- [Render Environment Variables](https://render.com/docs/environment-variables)
- [Docker Environment Variables](https://docs.docker.com/compose/environment-variables/)