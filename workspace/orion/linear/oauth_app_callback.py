"""One-shot OAuth callback for the Linear 'raymond' app (actor=app).
Listens on 127.0.0.1:8645, checks state, exchanges the code, writes the token to
~/.hermes/profiles/raymond/secrets/linear-app-token.json (0600), then exits.
Client id/secret come from env LINEAR_CID / LINEAR_CS (read from 1Password by the caller)."""
import http.server, json, os, sys, urllib.parse, urllib.request, time

STATE = os.environ['LINEAR_STATE']
REDIRECT = os.environ['LINEAR_REDIRECT']
CID, CS = os.environ['LINEAR_CID'], os.environ['LINEAR_CS']
OUT = os.path.expanduser('~/.hermes/profiles/raymond/secrets/linear-app-token.json')
done = {'ok': False}


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, msg):
        self.send_response(code)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(msg.encode())

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path != '/linear/oauth/callback':
            return self._send(404, 'not found')
        q = dict(urllib.parse.parse_qsl(u.query))
        if q.get('state') != STATE or 'code' not in q:
            print('callback rejected: bad state or no code', q.get('error'), flush=True)
            return self._send(400, 'bad request')
        data = urllib.parse.urlencode({'grant_type': 'authorization_code', 'code': q['code'],
                                       'redirect_uri': REDIRECT, 'client_id': CID,
                                       'client_secret': CS}).encode()
        try:
            with urllib.request.urlopen(urllib.request.Request(
                    'https://api.linear.app/oauth/token', data=data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}), timeout=30) as r:
                tok = json.loads(r.read())
        except urllib.error.HTTPError as e:
            print('token exchange failed', e.code, e.read()[:300], flush=True)
            return self._send(500, 'token exchange failed - tell Raymond')
        tok['obtained_at'] = time.time()
        fd = os.open(OUT, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w') as f:
            json.dump(tok, f)
        print('token saved; keys:', sorted(k for k in tok if k not in ('access_token', 'refresh_token')),
              'scope:', tok.get('scope'), 'expires_in:', tok.get('expires_in'), flush=True)
        done['ok'] = True
        self._send(200, 'Raymond app authorized. You can close this tab.')


srv = http.server.HTTPServer(('127.0.0.1', 8645), H)
srv.timeout = 5
deadline = time.time() + 1800
while not done['ok'] and time.time() < deadline:
    srv.handle_request()
print('exit ok' if done['ok'] else 'timed out', flush=True)
