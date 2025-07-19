# OrCast Cloudflare Deployment Checklist

## Quick Start

### 1. Prerequisites ✅
- [ ] Cloudflare account with `orcast.org` domain
- [ ] Node.js 18+ installed
- [ ] npm package manager

### 2. Automated Setup (Recommended) 🚀
```bash
# Run the automated deployment script
./deploy_cloudflare.sh
```

### 3. Manual Setup (Alternative) 🔧

#### Step 1: Install Dependencies
```bash
npm install
npm install -g wrangler
```

#### Step 2: Login to Cloudflare
```bash
wrangler login
```

#### Step 3: Get Zone ID
1. Go to Cloudflare dashboard
2. Click on `orcast.org` domain
3. Copy Zone ID from right sidebar
4. Update `wrangler.toml` with your Zone ID

#### Step 4: Create KV Namespaces
```bash
# Create production namespace
wrangler kv:namespace create CACHE

# Create preview namespace  
wrangler kv:namespace create CACHE --preview
```
Update `wrangler.toml` with the returned namespace IDs

#### Step 5: Set Environment Variables (Optional)
```bash
wrangler secret put GOOGLE_MAPS_API_KEY
wrangler secret put OPENWEATHER_API_KEY
wrangler secret put BIGQUERY_PROJECT_ID
```

#### Step 6: Deploy
```bash
# Deploy to production
npm run deploy:production

# Or deploy to staging
npm run deploy:staging
```

## Verification Steps

### After Deployment
- [ ] Visit `https://orcast.org/health` - should return "OK"
- [ ] Visit `https://orcast.org/api/predictions` - should return JSON
- [ ] Visit `https://orcast.org` - should load the full app

### Cloudflare Dashboard
- [ ] Check Workers tab for deployment status
- [ ] Verify custom domain routing
- [ ] Enable SSL/TLS "Full (strict)" mode
- [ ] Enable "Always Use HTTPS"

## Domain Configuration

### DNS Settings
- [ ] A record: `orcast.org` → Cloudflare proxy (orange cloud)
- [ ] CNAME record: `www.orcast.org` → `orcast.org`

### SSL/TLS Settings
- [ ] SSL/TLS mode: "Full (strict)"
- [ ] "Always Use HTTPS": Enabled
- [ ] HSTS: Enabled (optional)

## API Endpoints Available

After deployment, these endpoints will be live:

- `GET /api/sightings` - Recent orca sightings
- `POST /api/sightings` - Add new sighting
- `GET /api/predictions` - Behavior predictions
- `GET /api/behavioral-analysis` - Behavioral analysis
- `GET /api/dtag-data` - DTAG deployment data
- `GET /api/real-time-data` - Real-time environmental data
- `GET /api/feeding-zones` - Feeding zone information

## Performance Features

- ✅ Global CDN with edge caching
- ✅ Auto-scaling based on traffic
- ✅ DDoS protection
- ✅ Hourly data collection via cron jobs
- ✅ KV caching for optimal performance

## Monitoring Commands

```bash
# View real-time logs
wrangler tail

# View production logs
wrangler tail --env production

# Check deployment status
wrangler deployments list
```

## Troubleshooting

### Common Issues
- **Zone ID Error**: Update `wrangler.toml` with your actual zone ID
- **KV Namespace Error**: Create namespaces and update IDs
- **SSL Issues**: Set SSL to "Full (strict)" in Cloudflare dashboard
- **Route Conflicts**: Check for other workers using same routes

### Debug Commands
```bash
# Test locally
npm run dev

# Preview deployment
npm run preview

# Check authentication
wrangler whoami

# List KV namespaces
wrangler kv:namespace list
```

## Post-Deployment Tasks

### Immediate
- [ ] Test all API endpoints
- [ ] Verify frontend loads correctly
- [ ] Check mobile responsiveness
- [ ] Test PWA features

### Ongoing
- [ ] Monitor analytics in Cloudflare dashboard
- [ ] Set up uptime monitoring
- [ ] Configure analytics tracking
- [ ] Set up error reporting

## Support

For issues:
1. Check the `CLOUDFLARE_DEPLOYMENT.md` guide
2. Review Cloudflare Workers documentation
3. Check Cloudflare community forums
4. Contact Cloudflare support for critical issues

---

**🎉 Congratulations! Your OrCast app is now live at `orcast.org`!**

Share your orca behavioral analysis platform with the marine conservation community! 