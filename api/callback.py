"""Admin login, step 2: GitHub sends the admin back here; hand the login to the admin page.

Only people who can write to the GitHub repository can save anything, so the admin is yours alone.
"""
import os, json, urllib.request
from http.server import BaseHTTPRequestHandler
from http.cookies import SimpleCookie
from urllib.parse import urlencode, urlparse, parse_qs

PAGE = '''<!doctype html><html><head><meta charset="utf-8"><title>Signing in…</title></head>
<body style="font-family:sans-serif;padding:2rem">Signing in…
<script>
(function () {
  var msg = %s;
  function ok(origin) { return origin === location.origin || /^http:\\/\\/(localhost|127\\.0\\.0\\.1)(:\\d+)?$/.test(origin); }
  window.addEventListener('message', function (e) {
    if (!ok(e.origin)) return;
    window.opener.postMessage(msg, e.origin);
    setTimeout(function () { window.close(); }, 300);
  }, false);
  if (window.opener) window.opener.postMessage('authorizing:github', '*');
  else document.body.textContent = 'Please open the admin at /admin and click "Login with GitHub".';
})();
</script></body></html>'''


def result(status, payload):
    return 'authorization:github:%s:%s' % (status, json.dumps(payload))


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = parse_qs(urlparse(self.path).query)
        code, state = q.get('code', [''])[0], q.get('state', [''])[0]
        cookie = SimpleCookie(self.headers.get('cookie', ''))
        expected = cookie['cms_oauth_state'].value if 'cms_oauth_state' in cookie else ''
        if not code or not state or state != expected:
            msg = result('error', {'message': 'Login expired or was interrupted. Please try again.'})
        else:
            try:
                req = urllib.request.Request(
                    'https://github.com/login/oauth/access_token',
                    data=urlencode({'client_id': os.environ['OAUTH_CLIENT_ID'],
                                    'client_secret': os.environ['OAUTH_CLIENT_SECRET'],
                                    'code': code}).encode(),
                    headers={'Accept': 'application/json'})
                data = json.load(urllib.request.urlopen(req, timeout=15))
                if data.get('access_token'):
                    msg = result('success', {'token': data['access_token'], 'provider': 'github'})
                else:
                    msg = result('error', {'message': data.get('error_description', 'GitHub refused the login.')})
            except Exception as ex:  # noqa: BLE001
                msg = result('error', {'message': 'Login failed: %s' % ex.__class__.__name__})
        body = (PAGE % json.dumps(msg).replace('</', '<\\/')).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Set-Cookie', 'cms_oauth_state=; Path=/api; Max-Age=0; HttpOnly; Secure; SameSite=Lax')
        self.end_headers()
        self.wfile.write(body)
