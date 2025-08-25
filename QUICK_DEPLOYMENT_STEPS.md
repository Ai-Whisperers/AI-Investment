# Quick Deployment Steps - Waardhaven AutoIndex

## ✅ What's Ready
- Google OAuth authentication fully implemented
- Backend and frontend OAuth flow complete
- All environment variables documented
- render.yaml configured for deployment
- Deployment scripts prepared

## 🚀 Deploy Now - 5 Steps

### Step 1: Get API Keys (30 mins)
1. **TwelveData**: https://twelvedata.com/signup (Free tier: 800 calls/day)
2. **MarketAux**: https://www.marketaux.com/register (Free tier: 100 calls/day)
3. **Reddit**: https://www.reddit.com/prefs/apps → Create app (script type)
4. **YouTube**: https://console.cloud.google.com → Enable YouTube Data API
5. **Google OAuth**: Same console → Create OAuth 2.0 credentials
6. **Discord**: Server Settings → Integrations → Webhooks → New Webhook

### Step 2: Configure Render (10 mins)
1. Go to https://dashboard.render.com
2. Connect your GitHub repository
3. Click "New Blueprint Instance"
4. Select your repo and `render.yaml` file
5. Add environment variables:
   ```
   SECRET_KEY=<run: openssl rand -hex 32>
   GOOGLE_CLIENT_ID=<from Google Console>
   GOOGLE_CLIENT_SECRET=<from Google Console>
   GOOGLE_REDIRECT_URI=https://your-api.onrender.com/api/v1/auth/google/callback
   TWELVEDATA_API_KEY=<your key>
   MARKETAUX_API_KEY=<your key>
   REDDIT_CLIENT_ID=<your id>
   REDDIT_CLIENT_SECRET=<your secret>
   YOUTUBE_API_KEY=<your key>
   DISCORD_WEBHOOK=<your webhook url>
   FRONTEND_URL=https://your-web.onrender.com
   ```

### Step 3: Deploy Services (5 mins)
1. Click "Create New Resources"
2. Wait for build to complete (~5-10 mins)
3. Services will auto-deploy:
   - Backend: waardhaven-api
   - Frontend: waardhaven-web
   - Database: waardhaven-db

### Step 4: Run Migrations (2 mins)
1. Open Render Shell for `waardhaven-api`
2. Run:
   ```bash
   cd apps/api
   alembic upgrade head
   ```

### Step 5: Verify Deployment (5 mins)
1. Check health: `https://your-api.onrender.com/health`
2. View API docs: `https://your-api.onrender.com/docs`
3. Test frontend: `https://your-web.onrender.com`
4. Try Google login
5. Check monitoring dashboard

## 🎯 Post-Deployment

### Enable Data Collection
1. GitHub Actions → Settings → Secrets
2. Add same API keys as secrets
3. Enable workflows in Actions tab
4. Manual trigger: "Collect Investment Signals"

### Monitor Performance
- Discord channel will receive extreme signal alerts
- Dashboard: `/dashboard/monitoring`
- News feed: `/dashboard/news-feed`
- Signals: `/dashboard/extreme-signals`

## 📊 Expected Results
- **Hour 1**: System deployed and running
- **Day 1**: First signals detected
- **Week 1**: 20-30 signals generated
- **Month 1**: Portfolio recommendations active

## 🆘 Troubleshooting
- **Build fails**: Check logs in Render dashboard
- **Auth fails**: Verify Google OAuth redirect URI matches
- **No data**: Check API keys are correctly set
- **Database error**: Run migrations again

## 📝 Next Steps After Deployment
1. Monitor system health for 24 hours
2. Verify signal collection is working
3. Test Discord notifications
4. Review first investment recommendations
5. Begin portfolio simulation

---

**Ready to deploy?** Start with Step 1 above. Total time: ~1 hour

For detailed instructions: `docs/DEPLOYMENT_GUIDE_2025.md`