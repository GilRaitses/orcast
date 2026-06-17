/**
 * ORCAST Cloudflare worker — serves static assets and proxies API traffic to App Runner.
 */
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const backendBase = (env.API_BASE_URL || 'https://BACKEND_URL_PLACEHOLDER').replace(/\/$/, '');

    if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/forecast/') || url.pathname === '/health') {
      const target = `${backendBase}${url.pathname}${url.search}`;
      const proxied = new Request(target, {
        method: request.method,
        headers: request.headers,
        body: request.method === 'GET' || request.method === 'HEAD' ? undefined : request.body,
        redirect: 'follow'
      });
      const response = await fetch(proxied);
      const headers = new Headers(response.headers);
      headers.set('Access-Control-Allow-Origin', '*');
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers
      });
    }

    return new Response('ORCAST frontend is deployed separately; API proxy is active.', {
      status: 200,
      headers: { 'content-type': 'text/plain' }
    });
  }
};
