# Deployment Checklist for Render.com

## Prerequisites
- [ ] GitHub repository connected to Render
- [ ] Render account with Starter plan or higher
- [ ] TwelveData API key (free tier available)
- [ ] MarketAux API key (optional)

## Environment Variables to Set in Render

### Backend Service (waardhaven-api)
Required:
- [ ] `SECRET_KEY` - Generate with: `openssl rand -hex 32`
- [ ] `DATABASE_URL` - Auto-populated from database connection
- [ ] `TWELVEDATA_API_KEY` - Your TwelveData API key
- [ ] `ADMIN_TOKEN` - Generate secure token for admin endpoints

Optional:
- [ ] `SKIP_STARTUP_REFRESH=true` - Skip initial data load (faster startup)
- [ ] `DEBUG_MODE=false` - Disable debug logging in production
- [ ] `REDIS_URL` - For background tasks (if using Redis)
- [ ] `MARKETAUX_API_KEY` - For news data (if available)

### Frontend Service (waardhaven-web)
- [ ] `NEXT_PUBLIC_API_URL` - URL of deployed backend service

## Deployment Steps

### 1. Initial Setup
1. Fork/clone repository to your GitHub account
2. Connect GitHub repository to Render
3. Create new Web Service from repository

### 2. Database Setup
1. Create PostgreSQL database in Render
2. Note the connection string (auto-populated as DATABASE_URL)
3. Database will auto-initialize on first startup

### 3. Backend Deployment
1. Select "waardhaven-api" service
2. Set environment variables (see above)
3. Deploy service
4. Wait for health check to pass
5. Test API at: `https://your-api-url.onrender.com/api/v1/health`

### 4. Frontend Deployment
1. Select "waardhaven-web" service
2. Set `NEXT_PUBLIC_API_URL` to backend URL
3. Deploy service
4. Access at: `https://your-web-url.onrender.com`

### 5. Post-Deployment Verification
- [ ] API health check passes
- [ ] Database tables created
- [ ] Can register new user
- [ ] Can login with credentials
- [ ] Portfolio creation works
- [ ] Market data loads (if API key provided)

## Monitoring & Maintenance

### Health Checks
- Backend: `/api/v1/health`
- Database: `/api/v1/diagnostics/database`
- Market data: `/api/v1/diagnostics/market-data`

### Manual Operations
- Trigger data refresh: `POST /api/v1/manual/trigger-refresh`
- View system status: `GET /api/v1/diagnostics/status`

### Logs
- Check Render dashboard for service logs
- Backend startup logs show initialization status
- Look for "Starting uvicorn server" message

## Troubleshooting

### Common Issues

1. **Database connection fails**
   - Verify DATABASE_URL is set correctly
   - Check database is provisioned and running
   - Wait 1-2 minutes for cold start

2. **Market data not loading**
   - Verify TWELVEDATA_API_KEY is set
   - Check API key validity at twelvedata.com
   - Try manual refresh endpoint

3. **Frontend can't connect to backend**
   - Verify NEXT_PUBLIC_API_URL includes https://
   - Check CORS settings allow frontend domain
   - Test API directly in browser

4. **Slow startup times**
   - Set SKIP_STARTUP_REFRESH=true
   - Data will load on first request instead

## Security Checklist
- [ ] Strong SECRET_KEY (32+ characters)
- [ ] ADMIN_TOKEN is unique and secure
- [ ] Database has automatic backups enabled
- [ ] HTTPS enforced (automatic on Render)
- [ ] Environment variables marked as secret

## Performance Optimization
- [ ] Enable Redis for caching (optional)
- [ ] Set appropriate rate limits for APIs
- [ ] Monitor memory usage in Render dashboard
- [ ] Scale to multiple instances if needed

## Zero-Budget Deployment Tips
1. Use Render's free PostgreSQL tier initially
2. TwelveData free tier: 800 API calls/day
3. Skip Redis initially (not required)
4. Use single instance per service
5. Enable auto-sleep to save resources

## Next Steps After Deployment
1. Create first portfolio
2. Configure investment strategies
3. Load historical data (automatic)
4. Monitor performance metrics
5. Set up alerts (optional)