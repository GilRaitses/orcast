# OrCast Cloudflare Deployment Guide

## Prerequisites

1. **Cloudflare Account** with `orcast.org` domain registered
2. **Node.js** version 18 or higher
3. **npm** package manager
4. **Wrangler CLI** (Cloudflare Workers CLI)

## Setup Instructions

### 1. Install Dependencies

```bash
# Install Node.js dependencies
npm install

# Install Wrangler CLI globally (if not already installed)
npm install -g wrangler
```

### 2. Cloudflare Authentication

```bash
# Login to Cloudflare
wrangler login

# Verify authentication
wrangler whoami
```

### 3. Get Cloudflare Configuration IDs

You'll need to get these from your Cloudflare dashboard:

**Get Zone ID:**
1. Go to Cloudflare dashboard
2. Select your `orcast.org` domain
3. Copy the Zone ID from the right sidebar

**Create KV Namespace:**
```bash
# Create production KV namespace
wrangler kv:namespace create CACHE

# Create preview KV namespace
wrangler kv:namespace create CACHE --preview
```

### 4. Update Configuration

Edit `wrangler.toml` and replace:
- `YOUR_ZONE_ID` with your actual zone ID
- `YOUR_KV_NAMESPACE_ID` with the production KV namespace ID
- `YOUR_KV_PREVIEW_ID` with the preview KV namespace ID

### 5. Deploy to Cloudflare

```bash
# Deploy to production
npm run deploy:production

# Or deploy to staging first
npm run deploy:staging
```

## Domain Configuration

### 1. DNS Settings

In your Cloudflare dashboard for `orcast.org`:

1. **DNS Records**: Make sure you have:
   - A record pointing to your Cloudflare proxy (orange cloud enabled)
   - CNAME record for `www` pointing to `orcast.org`

2. **SSL/TLS**: 
   - Set to "Full (strict)" for optimal security
   - Enable "Always Use HTTPS"

### 2. Workers Routes

The worker will automatically be deployed to:
- **Production**: `orcast.org/*`
- **Staging**: `staging.orcast.org/*` (if you create this subdomain)

## Environment Variables

Set these in your Cloudflare Workers dashboard:

```bash
# Set environment variables
wrangler secret put GOOGLE_MAPS_API_KEY
wrangler secret put OPENWEATHER_API_KEY
wrangler secret put BIGQUERY_PROJECT_ID
```

## Verification

After deployment:

1. **Check Health**: Visit `https://orcast.org/health` - should return "OK"
2. **Check API**: Visit `https://orcast.org/api/predictions` - should return JSON
3. **Check App**: Visit `https://orcast.org` - should load the full application

## Features Enabled

### Frontend Features
- **Static Asset Serving**: All CSS, JS, and HTML files
- **PWA Support**: Manifest.json and service worker capabilities
- **SPA Routing**: Single Page Application routing support
- **Security Headers**: HSTS, CSP, and other security headers

### Backend Features
- **API Endpoints**: All existing API functionality
- **KV Caching**: High-performance caching for predictions and data
- **Scheduled Tasks**: Hourly data collection and updates
- **Real-time Data**: Weather, tides, and sighting information
- **DTAG Integration**: Behavioral analysis and dive detection

### Performance Features
- **Global CDN**: Cloudflare's global edge network
- **Auto-scaling**: Automatic scaling based on traffic
- **Edge Caching**: Intelligent caching at edge locations
- **DDoS Protection**: Built-in DDoS mitigation

## Monitoring and Maintenance

### 1. View Logs

```bash
# View real-time logs
wrangler tail

# View logs for specific environment
wrangler tail --env production
```

### 2. Analytics

Monitor your app in the Cloudflare dashboard:
- **Analytics Tab**: Traffic, requests, and performance metrics
- **Workers Analytics**: Function execution time and errors
- **Security Tab**: Security events and threats blocked

### 3. Updates

To update the application:

```bash
# Update the code
# Make your changes to src/index.js or public/ files

# Deploy updates
npm run deploy:production
```

## Troubleshooting

### Common Issues

1. **Zone ID Error**: Make sure you've updated `wrangler.toml` with your actual zone ID
2. **KV Namespace Error**: Create KV namespaces and update the IDs in configuration
3. **Route Conflicts**: Ensure no other workers are using the same routes
4. **SSL Issues**: Make sure SSL is set to "Full (strict)" in Cloudflare

### Debug Commands

```bash
# Test locally
npm run dev

# Preview deployment
npm run preview

# Check configuration
wrangler whoami
wrangler kv:namespace list
```

## API Endpoints

Your deployed app will have these endpoints:

- `GET /api/sightings` - Get recent orca sightings
- `POST /api/sightings` - Add new sighting
- `GET /api/predictions` - Get behavior predictions
- `GET /api/behavioral-analysis` - Get behavioral analysis
- `GET /api/dtag-data` - Get DTAG deployment data
- `GET /api/real-time-data` - Get real-time environmental data
- `GET /api/feeding-zones` - Get feeding zone information

## Performance Optimization

### Caching Strategy
- **Predictions**: Cached for 1 hour
- **Behavioral Analysis**: Cached for 30 minutes
- **DTAG Data**: Cached for 2 hours
- **Feeding Zones**: Cached for 4 hours
- **Static Assets**: Cached for 5 minutes

### Scheduled Tasks
- **Data Collection**: Runs every hour
- **Cache Refresh**: Automatic cache invalidation
- **Analytics**: Performance metrics collection

## Security Features

### Headers
- **HSTS**: Strict Transport Security enabled
- **CSP**: Content Security Policy configured
- **XSS Protection**: Cross-site scripting protection
- **Frame Options**: Clickjacking protection

### Access Control
- **CORS**: Properly configured for API access
- **Rate Limiting**: Built-in through Cloudflare
- **DDoS Protection**: Automatic threat mitigation

## Cost Optimization

### Free Tier Limits
- **Requests**: 100,000 per day
- **CPU Time**: 10ms per request
- **KV Operations**: 1,000 per day
- **Storage**: 1GB KV storage

### Monitoring Usage
- Check Cloudflare dashboard for usage metrics
- Set up alerts for approaching limits
- Optimize code for performance

## Next Steps

1. **Custom Domain**: Configure custom domain routing
2. **SSL Certificate**: Set up SSL certificates
3. **Analytics**: Enable advanced analytics
4. **Monitoring**: Set up uptime monitoring
5. **Backup**: Configure data backup strategies

## Support

For issues:
1. Check Cloudflare Workers documentation
2. Review Cloudflare community forums
3. Contact Cloudflare support for critical issues

---

**Your OrCast app is now deployed to `orcast.org` with full Cloudflare Workers integration!** 