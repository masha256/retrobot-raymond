"""Minimal Linear MCP client (streamable HTTP) using Raymond's stored OAuth token.
Used until the session reloads the native mcp_linear_* tools."""
import json, os, sys, urllib.request

TOK = json.load(open(os.path.expanduser('~/.hermes/profiles/raymond/mcp-tokens/linear.json')))['access_token']
URL = 'https://mcp.linear.app/mcp'
_sid = None
_id = 0


def _post(payload):
    global _sid
    h = {'Authorization': f'Bearer {TOK}', 'Content-Type': 'application/json',
         'Accept': 'application/json, text/event-stream'}
    if _sid:
        h['Mcp-Session-Id'] = _sid
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers=h, method='POST')
    with urllib.request.urlopen(req, timeout=60) as r:
        _sid = r.headers.get('Mcp-Session-Id') or _sid
        body = r.read().decode()
        ct = r.headers.get('Content-Type', '')
    if not body.strip():
        return None
    if 'event-stream' in ct:
        out = None
        for line in body.splitlines():
            if line.startswith('data:'):
                m = json.loads(line[5:].strip())
                if 'id' in m:
                    out = m
        return out
    return json.loads(body)


def rpc(method, params=None):
    global _id
    _id += 1
    r = _post({'jsonrpc': '2.0', 'id': _id, 'method': method, 'params': params or {}})
    if r and 'error' in r:
        raise RuntimeError(r['error'])
    return r['result'] if r else None


def init():
    rpc('initialize', {'protocolVersion': '2025-03-26', 'capabilities': {},
                       'clientInfo': {'name': 'raymond-lmcp', 'version': '0.1'}})
    _post({'jsonrpc': '2.0', 'method': 'notifications/initialized'})


def call(name, **args):
    r = rpc('tools/call', {'name': name, 'arguments': args})
    txt = '\n'.join(c.get('text', '') for c in r.get('content', []))
    if r.get('isError'):
        raise RuntimeError(f'{name}: {txt}')
    try:
        return json.loads(txt)
    except Exception:
        return txt


if __name__ == '__main__':
    init()
    for t in rpc('tools/list')['tools']:
        print(t['name'], '|', json.dumps(t['inputSchema'].get('properties', {}))[:300])
