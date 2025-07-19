# Custom Domain Setup for OrCast Workers

## Issue: orcast.org "Can't be reached"

The DNS records are correct, but custom domains for Workers need additional configuration in the Cloudflare dashboard.

## Solution: Add Custom Domain in Workers Dashboard

### Step 1: Access Workers Dashboard
1. Go to https://dash.cloudflare.com
2. Click **Workers & Pages** (left sidebar)
3. Click **orcast-app** (your Worker)
4. Click **Settings** tab
5. Scroll down to **Domains & Routes**

### Step 2: Add Custom Domain
1. Click **Add Custom Domain**
2. Enter: `orcast.org`
3. Click **Add Domain**
4. Cloudflare will verify the domain and create the necessary configuration

### Step 3: Alternative - Use Routes
If custom domain doesn't work, try adding a route:
1. In **Domains & Routes** section
2. Click **Add Route**
3. Enter: `orcast.org/*`
4. Select your Worker: `orcast-app`
5. Click **Add Route**

### Step 4: SSL/TLS Configuration
1. Go to **SSL/TLS** → **Overview**
2. Set encryption mode to **"Full (strict)"**
3. Go to **SSL/TLS** → **Edge Certificates**
4. Enable **"Always Use HTTPS"**
5. Enable **"Automatic HTTPS Rewrites"**

### Step 5: Deploy with Custom Domain
After dashboard setup, deploy again:
```bash
npx wrangler deploy --env production
```

## Verification Steps

### Test 1: Health Check
```bash
curl https://orcast.org/health
# Should return: OK
```

### Test 2: API Endpoint
```bash
curl https://orcast.org/api/predictions
# Should return: JSON with predictions
```

### Test 3: Browser Test
Visit https://orcast.org - should show OrCast homepage

## Common Issues

### Issue: "Custom domain not found"
**Solution**: Make sure the domain is added in Workers dashboard, not just DNS

### Issue: "SSL certificate error"
**Solution**: 
1. Check SSL/TLS mode is "Full (strict)"
2. Wait 5-10 minutes for SSL provisioning
3. Try HTTP first: http://orcast.org/health

### Issue: "Route not working"
**Solution**: 
1. Delete any existing routes
2. Add new route: `orcast.org/*`
3. Ensure it's linked to `orcast-app` worker

## Alternative: Test with workers.dev

To verify the Worker is working, you can test with the workers.dev subdomain:

1. Go to Workers dashboard
2. Click **orcast-app**
3. Look for the **workers.dev** URL
4. Test: `https://orcast-app.YOUR-SUBDOMAIN.workers.dev/health`

## Expected Results

Once configured correctly:
- **https://orcast.org** → OrCast homepage
- **https://orcast.org/health** → "OK"
- **https://orcast.org/api/predictions** → JSON predictions
- **https://orcast.org/api/sightings** → JSON sightings

## Support

If issues persist:
1. Check Workers dashboard for error messages
2. Verify route is active and linked to correct worker
3. Check SSL certificate status
4. Try accessing via workers.dev subdomain first

---

**The key is configuring the custom domain in the Workers dashboard, not just DNS records!** 