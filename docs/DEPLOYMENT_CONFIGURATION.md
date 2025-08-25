# Deployment Configuration Guide
*Last Updated: 2025-01-25*

## 🚀 Deployment Platform: Render.com

This guide documents all environment variables and configuration required for production deployment on Render.com.

---

## 🔐 Environment Variables

### Core Configuration

```bash
# Application Settings
ENVIRONMENT=production
APP_NAME=waardhaven-autoindex
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO

# Security
SECRET_KEY=<generate-secure-random-key>  # Use: openssl rand -hex 32
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS Settings
CORS_ORIGINS=["https://your-frontend-domain.com"]
CORS_ALLOW_CREDENTIALS=true
```

### Database Configuration

```bash
# PostgreSQL (Render provides this)
DATABASE_URL=<provided-by-render>

# Database Pool Settings
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true

# Test Database (optional)
TEST_DATABASE_URL=sqlite:///:memory:
```

### Cache Configuration

```bash
# Redis (using Redis Cloud free tier or Render Redis)
REDIS_URL=<redis-connection-string>
REDIS_MAX_CONNECTIONS=10
REDIS_SOCKET_TIMEOUT=5
REDIS_DECODE_RESPONSES=true

# Alternative Redis Providers (if not using Render)
UPSTASH_REDIS_URL=<upstash-url-if-using>
REDIS_CLOUD_URL=<redis-cloud-url-if-using>
```

### API Keys - Data Sources

```bash
# Market Data
TWELVEDATA_API_KEY=<your-api-key>
MARKETAUX_API_KEY=<your-api-key>

# Social Media APIs
REDDIT_CLIENT_ID=<your-client-id>
REDDIT_CLIENT_SECRET=<your-client-secret>
REDDIT_USER_AGENT=waardhaven-autoindex/1.0

# YouTube
YOUTUBE_API_KEY=<your-api-key>
YOUTUBE_DAILY_QUOTA=10000

# News APIs (optional)
NEWSAPI_KEY=<your-api-key>
ALPHAVANTAGE_API_KEY=<your-api-key>
```

### Authentication Providers

```bash
# Google OAuth
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-client-secret>
GOOGLE_REDIRECT_URI=https://your-domain.com/api/v1/auth/google/callback

# Session Management
SESSION_SECRET_KEY=<generate-secure-key>
SESSION_TIMEOUT=1800  # 30 minutes
SECURE_COOKIES=true
```

### Notification Services

```bash
# Discord Webhooks
DISCORD_WEBHOOK=<your-discord-webhook-url>
DISCORD_ALERT_WEBHOOK=<critical-alerts-webhook>
DISCORD_RATE_LIMIT=30  # messages per minute

# Slack (optional)
SLACK_WEBHOOK=<your-slack-webhook-url>
SLACK_CHANNEL=#investments

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<your-email>
SMTP_PASSWORD=<app-specific-password>
FROM_EMAIL=alerts@waardhaven.com
```

### AI/ML Services

```bash
# OpenAI (for signal processing)
OPENAI_API_KEY=<your-api-key>
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_MAX_TOKENS=4000

# Anthropic Claude (optional)
ANTHROPIC_API_KEY=<your-api-key>
CLAUDE_MODEL=claude-3-opus-20240229

# AI Service Settings
AI_CONFIDENCE_THRESHOLD=0.8
AI_PROCESSING_BATCH_SIZE=50
AI_RETRY_ATTEMPTS=3
```

### Performance & Monitoring

```bash
# Sentry (optional)
SENTRY_DSN=<your-sentry-dsn>
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# Metrics
METRICS_ENABLED=true
HEALTH_CHECK_INTERVAL=60
ALERT_THRESHOLD_ERROR_RATE=0.05
ALERT_THRESHOLD_RESPONSE_TIME=1000
ALERT_THRESHOLD_MEMORY_USAGE=80
```

### Feature Flags

```bash
# Feature Toggles
ENABLE_EXTREME_SIGNALS=true
ENABLE_MEME_VELOCITY=true
ENABLE_AI_INSIGHTS=true
ENABLE_SOCIAL_SCRAPING=true
ENABLE_WEBSOCKETS=false  # Not yet implemented
ENABLE_PAPER_TRADING=false  # Not yet implemented
ENABLE_BACKTESTING=true
ENABLE_DISCORD_ALERTS=true
```

### Rate Limiting

```bash
# API Rate Limits
RATE_LIMIT_DEFAULT=100  # requests per minute
RATE_LIMIT_AUTHENTICATED=500
RATE_LIMIT_BURST=20

# External API Rate Limits
REDDIT_RATE_LIMIT=60  # per minute
YOUTUBE_RATE_LIMIT=100  # per day (free tier)
MARKETAUX_RATE_LIMIT=100  # per day (free tier)
TWELVEDATA_RATE_LIMIT=8  # per minute (free tier)
```

### Background Jobs

```bash
# Celery Configuration (if using)
CELERY_BROKER_URL=<redis-url>
CELERY_RESULT_BACKEND=<redis-url>
CELERY_TASK_TIME_LIMIT=300
CELERY_TASK_SOFT_TIME_LIMIT=240

# Scheduled Tasks
ENABLE_SCHEDULED_COLLECTION=true
COLLECTION_SCHEDULE_HOURS=6,13,20,3  # UTC
SIGNAL_PROCESSING_INTERVAL=300  # seconds
```

### Deployment Specific

```bash
# Render.com Specific
RENDER=true
RENDER_SERVICE_NAME=waardhaven-api
PORT=10000  # Render uses 10000

# Domain Configuration
API_BASE_URL=https://api.waardhaven.com
FRONTEND_URL=https://waardhaven.com
ALLOWED_HOSTS=["api.waardhaven.com", "waardhaven.com"]

# Static Files
STATIC_URL=/static/
MEDIA_URL=/media/
```

### Testing & Development

```bash
# Only set these in development/staging
TESTING=false
SKIP_STARTUP_REFRESH=false
SQL_ECHO=false
SQL_ECHO_POOL=false
DEBUG_POOL=false
MOCK_EXTERNAL_APIS=false
```

---

## 📝 Render.com Configuration

### Web Service Settings

```yaml
Name: waardhaven-api
Environment: Python 3
Build Command: cd apps/api && pip install -r requirements.txt
Start Command: cd apps/api && uvicorn app.main:app --host 0.0.0.0 --port $PORT
Health Check Path: /health
Auto-Deploy: Yes (from main branch)
```

### Static Site Settings (Frontend)

```yaml
Name: waardhaven-web
Environment: Node
Build Command: cd apps/web && npm install && npm run build
Publish Directory: apps/web/.next
Routes: /*    /index.html   200
```

### Background Worker (Optional)

```yaml
Name: waardhaven-worker
Environment: Python 3
Build Command: cd apps/api && pip install -r requirements.txt
Start Command: cd apps/api && celery -A app.worker worker --loglevel=info
```

---

## 🔄 GitHub Actions Secrets

Add these secrets to your GitHub repository for CI/CD:

```yaml
# Same as above environment variables, plus:
RENDER_API_KEY=<your-render-api-key>
RENDER_SERVICE_ID=<your-service-id>
GITHUB_TOKEN=<automatically-provided>
CODECOV_TOKEN=<for-coverage-reports>
```

---

## 🚦 Pre-Deployment Checklist

### Required (MVP)
- [ ] Generate SECRET_KEY
- [ ] Configure DATABASE_URL (provided by Render)
- [ ] Add REDIS_URL
- [ ] Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET
- [ ] Set YOUTUBE_API_KEY
- [ ] Set MARKETAUX_API_KEY
- [ ] Set TWELVEDATA_API_KEY
- [ ] Configure DISCORD_WEBHOOK
- [ ] Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET

### Recommended
- [ ] Configure Sentry for error tracking
- [ ] Set up custom domain
- [ ] Enable SSL certificate
- [ ] Configure CORS_ORIGINS
- [ ] Set up health checks
- [ ] Configure auto-scaling rules

### Optional
- [ ] Add Slack webhook
- [ ] Configure email notifications
- [ ] Set up OpenAI/Anthropic keys
- [ ] Enable advanced monitoring

---

## 🔧 Configuration Commands

### Generate Secret Keys

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Or using OpenSSL
openssl rand -hex 32

# Generate SESSION_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Database Migration

```bash
# After deployment, run migrations
cd apps/api
alembic upgrade head

# Create initial admin user (optional)
python -m app.scripts.create_admin
```

### Verify Deployment

```bash
# Check health endpoint
curl https://your-api-domain.com/health

# Check API docs
open https://your-api-domain.com/docs

# Test authentication
curl -X POST https://your-api-domain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'
```

---

## 🚨 Important Security Notes

1. **Never commit secrets to version control**
2. **Use Render's environment variable UI to set sensitive values**
3. **Rotate API keys regularly**
4. **Use different keys for staging/production**
5. **Enable 2FA on all service accounts**
6. **Monitor API usage for anomalies**
7. **Set up alerts for failed authentication attempts**
8. **Use webhook signatures where available**

---

## 📊 Resource Requirements

### Minimum (Free/Starter Tier)
- **RAM**: 512MB
- **CPU**: 0.5 vCPU
- **Database**: 256MB PostgreSQL
- **Redis**: 30MB
- **Storage**: 1GB

### Recommended (Production)
- **RAM**: 2GB
- **CPU**: 1 vCPU
- **Database**: 1GB PostgreSQL
- **Redis**: 100MB
- **Storage**: 10GB

### Scale (High Traffic)
- **RAM**: 4GB+
- **CPU**: 2+ vCPU
- **Database**: 10GB+ PostgreSQL
- **Redis**: 500MB+
- **Storage**: 50GB+

---

## 🔄 Update Process

1. Update environment variables in Render dashboard
2. Trigger manual deploy or push to main branch
3. Monitor deployment logs
4. Run database migrations if needed
5. Verify health checks pass
6. Test critical endpoints
7. Monitor error rates for 30 minutes

---

## 📞 Support

### Render.com
- Dashboard: https://dashboard.render.com
- Status: https://status.render.com
- Docs: https://render.com/docs

### Our Application
- Health Check: `/health`
- API Docs: `/docs`
- Metrics: `/api/v1/monitoring/system/metrics`
- Admin: `/admin` (if enabled)

---

**Note**: This configuration is for Render.com deployment. Adjust accordingly if deploying to other platforms like Vercel, Railway, or Heroku.