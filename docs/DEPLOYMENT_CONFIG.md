# 🚀 Deployment Configuration Guide

## Overview
This document contains all environment variables required for deploying the Waardhaven AutoIndex platform. Each service requires specific configuration to function properly. **DO NOT commit actual values to the repository**.

## 🔐 Critical Security Variables

### Authentication & Security
```env
# JWT Authentication (REQUIRED)
SECRET_KEY=                    # Min 32 chars, use: openssl rand -hex 32
JWT_ALGORITHM=HS256           # Default: HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # Default: 24 hours

# Admin Access (REQUIRED for production)
ADMIN_TOKEN=                   # Min 32 chars, for admin endpoints
```

## 💾 Database Configuration

### PostgreSQL (REQUIRED)
```env
DATABASE_URL=                  # Format: postgresql://user:pass@host:port/dbname
                              # Example: postgresql://admin:password@db.render.com:5432/waardhaven_db
```

### Redis Cache (Optional but recommended)
```env
REDIS_URL=                     # Format: redis://user:pass@host:port/db
                              # Example: redis://default:password@redis.render.com:6379/0
CACHE_TTL_SECONDS=300         # Default: 5 minutes
CACHE_TTL_LONG_SECONDS=3600   # Default: 1 hour
```

## 📊 Market Data APIs

### TwelveData API (REQUIRED for market data)
```env
TWELVEDATA_API_KEY=            # Get from: https://twelvedata.com/account/api-keys
TWELVEDATA_PLAN=free          # Options: free, grow, pro, enterprise
TWELVEDATA_RATE_LIMIT=8       # Credits per minute based on plan
ENABLE_MARKET_DATA_CACHE=true # Enable caching to reduce API calls
```

### MarketAux News API (Optional)
```env
MARKETAUX_API_KEY=             # Get from: https://www.marketaux.com/account/dashboard
MARKETAUX_RATE_LIMIT=100      # Requests per minute
ENABLE_NEWS_CACHE=true        # Enable news caching
NEWS_REFRESH_INTERVAL=900     # Refresh interval in seconds (15 min)
```

## 🔍 OSINT & Alternative Data APIs

### Free Finance APIs (Optional - for enhanced data)
```env
# Alpha Vantage (5 calls/min, 500/day free)
ALPHA_VANTAGE_API_KEY=         # Get from: https://www.alphavantage.co/support/#api-key

# IEX Cloud (50,000 messages/month free)
IEX_CLOUD_API_KEY=             # Get from: https://iexcloud.io/console/tokens

# Polygon.io (5 calls/min free)
POLYGON_API_KEY=               # Get from: https://polygon.io/dashboard/api-keys

# Finnhub (60 calls/min free)
FINNHUB_API_KEY=               # Get from: https://finnhub.io/dashboard

# NewsAPI (500 requests/day free)
NEWSAPI_KEY=                   # Get from: https://newsapi.org/account

# CoinMarketCap (333 calls/day free)
COINMARKETCAP_API_KEY=         # Get from: https://pro.coinmarketcap.com/account
```

## 📱 Social Media Collection

### Reddit API (For social signal collection)
```env
REDDIT_CLIENT_ID=              # Get from: https://www.reddit.com/prefs/apps
REDDIT_CLIENT_SECRET=          # Create Reddit app as "script" type
```

### YouTube Data API v3
```env
YOUTUBE_API_KEY=               # Get from: https://console.cloud.google.com/apis/credentials
                              # Enable YouTube Data API v3, 10,000 units/day free
```

## 🤖 AI Services

### OpenAI (For signal processing)
```env
OPENAI_API_KEY=                # Get from: https://platform.openai.com/api-keys
```

### Anthropic Claude (Alternative/primary AI)
```env
ANTHROPIC_API_KEY=             # Get from: https://console.anthropic.com/account/keys
```

## 🔔 Alerting & Notifications

### Webhooks (Optional)
```env
SLACK_WEBHOOK=                 # For Slack alerts: https://api.slack.com/messaging/webhooks
DISCORD_WEBHOOK=               # For Discord alerts: Server Settings > Integrations > Webhooks
```

## 🌐 Frontend Configuration

### Next.js Frontend
```env
# API Connection (REQUIRED)
NEXT_PUBLIC_API_URL=           # Backend API URL
                              # Local: http://localhost:8000
                              # Production: https://api.yourdomain.com

# Google OAuth (Optional)
NEXT_PUBLIC_GOOGLE_CLIENT_ID=  # Get from: https://console.cloud.google.com/apis/credentials
                              # Configure OAuth consent screen first

# Analytics (Optional)
NEXT_PUBLIC_GA_ID=             # Google Analytics ID (format: G-XXXXXXXXXX)
```

## 🚀 Deployment Platform

### Render.com Specific
```env
# Auto-configured by Render
PORT=10000                     # Port for web services (auto-set by Render)
RENDER=true                    # Auto-set when running on Render
```

### Production Flags
```env
PRODUCTION=true                # Set for production deployments
DEBUG=false                    # Disable debug mode in production
NODE_ENV=production           # For frontend optimization
```

## ⚙️ Application Settings

### Performance & Behavior
```env
REFRESH_MODE=auto             # Options: auto, full, minimal, cached
SKIP_STARTUP_REFRESH=false    # Skip data refresh on startup
DAILY_DROP_THRESHOLD=-0.01    # Threshold for daily drop alerts

# Asset Configuration
ASSET_DEFAULT_START=2018-01-01 # Default start date for historical data
SP500_TICKER=^GSPC            # S&P 500 ticker symbol
```

### CORS Configuration
```env
FRONTEND_URL=                  # Frontend URL for CORS
                              # Example: https://waardhaven.yourdomain.com
```

## 📋 GitHub Actions Secrets

For automated signal collection, configure these in GitHub Settings > Secrets:

```yaml
# Required for signal collection workflow
DATABASE_URL
REDIS_URL
REDDIT_CLIENT_ID
REDDIT_CLIENT_SECRET
YOUTUBE_API_KEY
OPENAI_API_KEY
ANTHROPIC_API_KEY

# Optional for alerts
SLACK_WEBHOOK
DISCORD_WEBHOOK

# Optional for enhanced data
ALPHA_VANTAGE_API_KEY
IEX_CLOUD_API_KEY
POLYGON_API_KEY
FINNHUB_API_KEY
NEWSAPI_KEY
```

## 🔧 Environment File Templates

### Backend (.env)
```env
# apps/api/.env
SECRET_KEY=your-secret-key-min-32-chars
DATABASE_URL=postgresql://user:pass@host:5432/dbname
TWELVEDATA_API_KEY=your-twelvedata-key
REDIS_URL=redis://localhost:6379/0
ADMIN_TOKEN=your-admin-token-min-32-chars
SKIP_STARTUP_REFRESH=true
DEBUG=false
```

### Frontend (.env.local)
```env
# apps/web/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id
```

## 🚨 Security Best Practices

1. **Never commit real values** - Use `.env` files locally, environment variables in production
2. **Use strong secrets** - Minimum 32 characters for tokens/keys
3. **Rotate regularly** - Change SECRET_KEY and ADMIN_TOKEN every 90 days
4. **Limit API key permissions** - Use read-only keys where possible
5. **Monitor usage** - Check API quotas and rate limits regularly
6. **Use different keys per environment** - Separate dev/staging/production keys
7. **Enable 2FA** - On all API provider accounts
8. **Audit logs** - Monitor access to admin endpoints

## 🎯 Deployment Checklist

### Essential (Platform will not work without these)
- [ ] `SECRET_KEY` - Generated and secured
- [ ] `DATABASE_URL` - PostgreSQL connection configured
- [ ] `TWELVEDATA_API_KEY` - Market data API key obtained
- [ ] `NEXT_PUBLIC_API_URL` - Frontend knows backend URL

### Recommended (For full functionality)
- [ ] `ADMIN_TOKEN` - Admin endpoints secured
- [ ] `REDIS_URL` - Caching enabled
- [ ] `REDDIT_CLIENT_ID/SECRET` - Social signals enabled
- [ ] `YOUTUBE_API_KEY` - YouTube analysis enabled
- [ ] `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` - AI processing enabled

### Optional (Enhanced features)
- [ ] Alternative data APIs configured
- [ ] Webhook alerts setup
- [ ] Google OAuth configured
- [ ] Analytics tracking enabled

## 📊 Resource Limits

### Free Tier Quotas (Daily)
- **TwelveData**: 800 API credits (Free plan)
- **YouTube API**: 10,000 units
- **Reddit API**: 60 requests/minute
- **NewsAPI**: 500 requests
- **Alpha Vantage**: 500 requests
- **GitHub Actions**: 2000 minutes/month

### Rate Limiting
- Configure rate limits based on your API plan
- Use caching to reduce API calls
- Implement exponential backoff for failures
- Monitor quota usage in production

## 🔗 Quick Links

### API Key Registration
- [TwelveData](https://twelvedata.com/register)
- [MarketAux](https://www.marketaux.com/register)
- [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
- [IEX Cloud](https://iexcloud.io/sign-up)
- [Polygon.io](https://polygon.io/sign-up)
- [Finnhub](https://finnhub.io/register)
- [NewsAPI](https://newsapi.org/register)
- [Reddit Apps](https://www.reddit.com/prefs/apps)
- [Google Cloud Console](https://console.cloud.google.com/)
- [OpenAI](https://platform.openai.com/signup)
- [Anthropic](https://console.anthropic.com/signup)

### Deployment Platforms
- [Render Dashboard](https://dashboard.render.com/)
- [GitHub Actions](https://github.com/features/actions)
- [Vercel](https://vercel.com/) (Alternative for frontend)
- [Supabase](https://supabase.com/) (Alternative for database)

## 📝 Notes

1. **Development vs Production**: Some variables have different requirements in development vs production
2. **Free Tier Limits**: Most APIs have free tiers sufficient for MVP
3. **Fallback Mechanisms**: System uses multiple APIs with fallback for resilience
4. **Caching Strategy**: Enable all caches to minimize API usage
5. **Cost Optimization**: Start with free tiers, upgrade only when needed

---

**Last Updated**: January 2025
**Version**: 2.0.0
**Status**: Ready for deployment configuration