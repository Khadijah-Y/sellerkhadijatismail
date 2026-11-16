"""Admin login with a username and password.

Set these in Vercel (Settings → Environment Variables). They are never in the code or the repo:
  ADMIN_USERNAME   the username you log in with
  ADMIN_PASSWORD   a long, unique password
  GITHUB_TOKEN     a fine-grained GitHub token with "Contents: Read and write" on this repository only
On a correct login the admin receives the token so it can save your changes to GitHub.
"""
import os, json, time, hmac
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def _send(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        user, pw, token = (os.environ.get(k, '') for k in ('ADMIN_USERNAME', 'ADMIN_PASSWORD', 'GITHUB_TOKEN'))
        if not (user and pw and token):
            return self._send(503, {'error': 'Username login is not set up yet. Add ADMIN_USERNAME, ADMIN_PASSWORD and GITHUB_TOKEN in Vercel.'})
        try:
            n = min(int(self.headers.get('content-length') or 0), 4096)
            data = json.loads(self.rfile.read(n) or b'{}')
        except Exception:  # noqa: BLE001
            return self._send(400, {'error': 'Bad request.'})
        ok_user = hmac.compare_digest(str(data.get('username', '')).strip().lower().encode(), user.strip().lower().encode())
        ok_pw = hmac.compare_digest(str(data.get('password', '')).encode(), pw.encode())
        if not (ok_user and ok_pw):
            time.sleep(1.5)   # slows down password guessing
            return self._send(401, {'error': 'Wrong username or password.'})
        return self._send(200, {'token': token})

    def do_GET(self):
        self._send(405, {'error': 'Use POST.'})
