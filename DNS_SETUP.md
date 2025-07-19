# DNS Setup Guide for orcast.org

## Current Status
✅ **OrCast Worker deployed successfully**  
✅ **Route configured**: `orcast.org/*`  
⚠️ **DNS setup needed**: Domain not yet accessible

## DNS Configuration Steps

### 1. Access Cloudflare Dashboard
1. Go to https://dash.cloudflare.com
2. Select your `orcast.org` domain
3. Click on the **DNS** tab

### 2. Set Up DNS Records

**Required DNS Records:**

#### A Record (Primary)
- **Type**: A
- **Name**: `@` (root domain)
- **Content**: `192.0.2.1` (placeholder IP)
- **Proxy Status**: ✅ **Proxied (Orange Cloud)**
- **TTL**: Auto

#### CNAME Record (WWW)
- **Type**: CNAME
- **Name**: `www`
- **Content**: `orcast.org`
- **Proxy Status**: ✅ **Proxied (Orange Cloud)**
- **TTL**: Auto

### 3. Workers Route Configuration

The Workers route is already configured:
- **Route**: `orcast.org/*`
- **Worker**: `orcast-app`
- **Environment**: production

### 4. SSL/TLS Settings

1. Go to **SSL/TLS** tab
2. Set **SSL/TLS encryption mode** to **"Full (strict)"**
3. Enable **"Always Use HTTPS"**
4. Enable **"Automatic HTTPS Rewrites"**

### 5. Page Rules (Optional)

Create a page rule to handle WWW redirects:
- **URL**: `www.orcast.org/*`
- **Setting**: Forwarding URL (301 - Permanent Redirect)
- **Destination**: `https://orcast.org/$1`

## Verification Steps

Once DNS is configured (may take 5-15 minutes):

### 1. Test Health Check
```bash
curl https://orcast.org/health
# Should return: OK
```

### 2. Test API Endpoints
```bash
# Test predictions API
curl https://orcast.org/api/predictions

# Test behavioral analysis
curl https://orcast.org/api/behavioral-analysis

# Test DTAG data
curl https://orcast.org/api/dtag-data
```

### 3. Test Main Site
Visit https://orcast.org in your browser - you should see the OrCast homepage.

## Common Issues & Solutions

### Issue: "DNS_PROBE_FINISHED_NXDOMAIN"
**Solution**: DNS records not set up or still propagating (wait 5-15 minutes)

### Issue: "This site can't provide a secure connection"
**Solution**: 
1. Check SSL/TLS is set to "Full (strict)"
2. Ensure "Always Use HTTPS" is enabled
3. Wait for SSL certificate provisioning

### Issue: "Worker threw exception"
**Solution**: Check worker logs:
```bash
npx wrangler tail --env production
```

### Issue: "Route not found"
**Solution**: Verify the route `orcast.org/*` is properly configured in Workers dashboard

## DNS Propagation Check

You can check DNS propagation status at:
- https://www.whatsmydns.net/
- https://dnschecker.org/

Search for `orcast.org` to see if it's resolving globally.

## Expected Results After Setup

Once DNS is properly configured, you should be able to access:

- **Main Site**: https://orcast.org
- **API Endpoints**: https://orcast.org/api/*
- **Health Check**: https://orcast.org/health

The site will show:
- OrCast homepage with whale icon
- Links to all API endpoints
- TagTools integration status
- Real-time API connectivity test

## Support

If you encounter issues:
1. Check the Cloudflare dashboard for error messages
2. Verify all DNS records are proxied (orange cloud)
3. Ensure SSL/TLS is set to "Full (strict)"
4. Check worker logs with `npx wrangler tail --env production`

---

**Your OrCast platform is deployed and ready! Just configure the DNS records above to make it accessible at orcast.org.** 