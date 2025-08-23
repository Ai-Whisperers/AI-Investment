#  Setting Up Real Market Data Connection

## Overview
The platform is now configured to use real market data from TwelveData API instead of placeholder data. This guide will help you set up your API connections to start receiving live market prices and signals.

## Quick Start (5 minutes)

### Step 1: Get Your Free TwelveData API Key
1. Go to [TwelveData Registration](https://twelvedata.com/register)
2. Sign up for a free account
3. Verify your email
4. Go to [API Keys Page](https://twelvedata.com/account/api-keys)
5. Copy your API key

### Step 2: Configure Environment Variables
1. Navigate to the backend directory:
   ```bash
   cd apps/api
   ```

2. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

3. Edit the `.env` file and add your API key:
   ```env
   TWELVEDATA_API_KEY=your_actual_api_key_here
   ```

### Step 3: Start the Backend
```bash
# Install dependencies if needed
pip install -r requirements.txt

# Start the API server
uvicorn app.main:app --reload
```

### Step 4: Verify Connection
Test the API connection by visiting:
```
http://localhost:8000/api/v1/signals/integrated/daily
```

You should see real-time prices instead of placeholder data!

## Free Tier Limits

### TwelveData (Market Data)
- **Daily Limit**: 800 API credits
- **Rate Limit**: 8 requests per minute
- **Data Coverage**: US stocks, ETFs, forex
- **Historical Data**: Up to 15 years
- **Real-time Quotes**: Yes
- **WebSocket**: Not available on free tier

### Optimization Tips
1. **Caching**: The system automatically caches prices for 5 minutes
2. **Batch Requests**: Group multiple symbols in one request when possible
3. **Off-Peak Hours**: Schedule heavy data pulls during market closed hours
4. **Smart Refresh**: Only refresh data for actively monitored symbols

## Optional: MarketAux News API

For news sentiment analysis, also set up MarketAux:

1. Register at [MarketAux](https://www.marketaux.com/register)
2. Get your API key from the dashboard
3. Add to `.env`:
   ```env
   MARKETAUX_API_KEY=your_marketaux_key_here
   ```

**Free Tier**: 100 requests/day, perfect for news sentiment

## Optional: Redis Cache

For better performance, install Redis locally:

### Windows
```bash
# Using WSL/Ubuntu
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

### Mac
```bash
brew install redis
brew services start redis
```

### Configure in `.env`:
```env
REDIS_URL=redis://localhost:6379/0
```

## API Response Format

When properly configured, the API will return real-time data:

```json
{
  "symbol": "AAPL",
  "price": 182.45,
  "change": 2.15,
  "percent_change": 1.19,
  "volume": 52341876,
  "timestamp": "2025-01-23T10:30:00Z"
}
```

## Troubleshooting

### "Using placeholder data" message
- **Cause**: API key not configured
- **Fix**: Ensure `TWELVEDATA_API_KEY` is set in `.env`

### Rate limit errors
- **Cause**: Exceeding 8 requests/minute
- **Fix**: The system automatically handles rate limiting with retry logic

### No data returned
- **Cause**: Invalid symbol or API issue
- **Fix**: Check symbol format (e.g., "AAPL" not "Apple")

### Connection refused
- **Cause**: Backend not running
- **Fix**: Start the backend with `uvicorn app.main:app --reload`

## Testing Real Data Integration

### 1. Test Price Endpoint
```bash
curl http://localhost:8000/api/v1/signals/momentum/short
```

### 2. Test Integrated Signals
```bash
curl http://localhost:8000/api/v1/signals/integrated/daily
```

### 3. Test Agro-Robotics with News
```bash
curl http://localhost:8000/api/v1/signals/agro/opportunities
```

## Production Deployment

For production on Render.com:

1. Add environment variables in Render Dashboard:
   - Go to your service settings
   - Add Environment Variables:
     - `TWELVEDATA_API_KEY`
     - `MARKETAUX_API_KEY` (optional)
     - `REDIS_URL` (if using Render Redis)

2. Deploy and verify:
   - Check logs for "TwelveData API connected"
   - Monitor API credit usage in TwelveData dashboard

## Monitoring API Usage

### TwelveData Dashboard
- View usage: [TwelveData Dashboard](https://twelvedata.com/account/dashboard)
- Track credits: Monitor daily credit consumption
- Set alerts: Configure usage alerts at 80% threshold

### Application Monitoring
The platform includes built-in monitoring:
```python
# Check rate limit status
GET /api/v1/diagnostics/rate-limit

# Check cache stats
GET /api/v1/diagnostics/cache-stats
```

## Next Steps

After connecting real data:

1. **Configure WebSocket** (Next TODO item)
   - Real-time price streaming
   - Live signal updates
   - Instant alert notifications

2. **Set Up Alerts**
   - Configure high-conviction signal alerts
   - Set price movement thresholds
   - Enable email/Discord notifications

3. **Start Backtesting**
   - Test strategies with historical data
   - Optimize signal parameters
   - Validate expected returns

## Cost Optimization

### Staying Within Free Tier
- **800 credits/day** = ~100 symbols with full day data
- **Smart Usage**:
  - Focus on top 20-30 high-conviction symbols
  - Use 5-minute cache effectively
  - Batch similar requests
  - Schedule intensive analysis for weekends

### When to Upgrade
Consider upgrading ($29/month) when:
- Monitoring >50 symbols actively
- Need WebSocket for real-time updates
- Want 1-minute interval data
- Require higher rate limits

## Support

### API Documentation
- [TwelveData Docs](https://twelvedata.com/docs)
- [MarketAux Docs](https://www.marketaux.com/documentation)

### Common Issues
- [TwelveData FAQ](https://twelvedata.com/faq)
- [API Status Page](https://status.twelvedata.com/)

### Community
- GitHub Issues: Report bugs in our repo
- Discord: Join investment strategy discussions

---

**Status**: TwelveData integration COMPLETE 
**Next**: WebSocket implementation for live updates
**Time Saved**: Using real data vs building scraper = 200+ hours