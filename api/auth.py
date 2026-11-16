"""Admin login, step 1: send the admin's browser to GitHub to sign in.

Needs two environment variables in Vercel (Settings → Environment Variables):
  OAUTH_CLIENT_ID      from your GitHub OAuth App
  OAUTH_CLIENT_SECRET  from your GitHub OAuth App
"""
import os, secrets
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlencode, urlparse, parse_qs


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        client_id = os.environ.get('OAUTH_CLIENT_ID')
        if not client_id:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'Login is not set up yet: add OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET in Vercel.')
            return
        q = parse_qs(urlparse(self.path).query)
        scope = q.get('scope', ['repo'])[0]
        state = secrets.token_urlsafe(24)
        host = self.headers.get('x-forwarded-host') or self.headers.get('host')
        params = {
            'client_id': client_id,
            'redirect_uri': f'https://{host}/api/callback',
            'scope': scope,
            'state': state,
        }
        self.send_response(302)
        self.send_header('Location', 'https://github.com/login/oauth/authorize?' + urlencode(params))
        self.send_header('Set-Cookie', f'cms_oauth_state={state}; Path=/api; Max-Age=600; HttpOnly; Secure; SameSite=Lax')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
