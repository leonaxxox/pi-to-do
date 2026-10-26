#!/usr/bin/env python3
"""Pi To-Do: syncs Microsoft To Do and serves the pink display on http://localhost:8080"""
import json, os, time, threading, datetime, urllib.request, urllib.parse, urllib.error
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, 'config.json')))
TOKEN_FILE = os.path.join(HERE, 'token.json')
AUTH = 'https://login.microsoftonline.com/common/oauth2/v2.0'
SCOPE = 'Tasks.ReadWrite User.Read offline_access'
GRAPH = 'https://graph.microsoft.com/v1.0'
PRI = {'high': 1, 'normal': 2, 'low': 3}

state = {'status': 'starting', 'tasks': [], 'login': None, 'error': None}
lock = threading.Lock()
wake = threading.Event()
tok = {}
q = lambda s: urllib.parse.quote(s, safe='')


def set_state(**kw):
    with lock:
        state.update(kw)


def post_form(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(), method='POST')
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return json.load(e)


def save_token(t):
    t['expires_at'] = time.time() + int(t.get('expires_in', 3600)) - 60
    tok.clear(); tok.update(t)
    with open(TOKEN_FILE, 'w') as fh:
        json.dump(t, fh)


def access_token():
    if not tok.get('refresh_token'):
        return None
    if time.time() < tok.get('expires_at', 0):
        return tok['access_token']
    r = post_form(AUTH + '/token', {'client_id': CFG['client_id'], 'grant_type': 'refresh_token',
                                    'refresh_token': tok['refresh_token'], 'scope': SCOPE})
    if 'access_token' in r:
        save_token(r)
        return r['access_token']
    if r.get('error') in ('invalid_grant', 'interaction_required'):
        tok.clear()
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
    return None


def device_login():
    r = post_form(AUTH + '/devicecode', {'client_id': CFG['client_id'], 'scope': SCOPE})
    if 'device_code' not in r:
        set_state(status='error', error=r.get('error_description', 'Sign-in failed'))
        print('Sign-in error:', r.get('error_description'))
        time.sleep(60)
        return
    print('Sign in at', r['verification_uri'], 'with code', r['user_code'])
    set_state(status='login', login={'code': r['user_code'], 'url': r['verification_uri']})
    interval = int(r.get('interval', 5))
    deadline = time.time() + int(r.get('expires_in', 900))
    while time.time() < deadline:
        time.sleep(interval)
        t = post_form(AUTH + '/token', {'client_id': CFG['client_id'], 'device_code': r['device_code'],
                                        'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'})
        if 'access_token' in t:
            save_token(t)
            set_state(status='ok', login=None)
            print('Signed in ♡')
            return
        if t.get('error') == 'slow_down':
            interval += 5
        elif t.get('error') != 'authorization_pending':
            break


def graph(method, path, body=None):
    at = access_token()
    if not at:
        raise PermissionError('not signed in')
    req = urllib.request.Request(path if path.startswith('http') else GRAPH + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Authorization': 'Bearer ' + at, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=20) as r:
        txt = r.read()
        return json.loads(txt) if txt else {}


def get_all(path):
    out, url = [], path
    while url:
        r = graph('GET', url)
        out += r.get('value', [])
        url = r.get('@odata.nextLink')
    return out


def due_label(d, today):
    if not d: return 'No date'
    if d < today: return 'Overdue'
    if d == today: return 'Today'
    if d == today + datetime.timedelta(days=1): return 'Tomorrow'
    return d.strftime('%a %-d %b')


def fetch_tasks():
    lists = [l for l in get_all('/me/todo/lists') if l.get('wellknownListName') != 'flaggedEmails']
    want = CFG.get('lists') or []
    if want:
        lists = [l for l in lists if l['displayName'] in want]
    today = datetime.date.today()
    out = []
    for l in lists:
        for t in get_all('/me/todo/lists/%s/tasks?$top=100' % q(l['id'])):
            done = t.get('status') == 'completed'
            if done and (t.get('completedDateTime') or {}).get('dateTime', '')[:10] != today.isoformat():
                continue
            d = (t.get('dueDateTime') or {}).get('dateTime', '')[:10]
            dd = datetime.date.fromisoformat(d) if d else None
            if CFG.get('only_due_today') and not done and (not dd or dd > today):
                continue
            out.append({'id': t['id'], 'listId': l['id'], 'title': t.get('title', ''), 'project': l['displayName'],
                        'due': due_label(dd, today), 'pri': PRI.get(t.get('importance'), 2), 'done': done})
    return out


def poller():
    if os.path.exists(TOKEN_FILE):
        tok.update(json.load(open(TOKEN_FILE)))
    while True:
        try:
            if not tok.get('refresh_token'):
                device_login()
                continue
            set_state(status='ok', tasks=fetch_tasks(), error=None)
        except PermissionError:
            time.sleep(10)
            continue
        except Exception as e:
            print('Sync error:', e)
            set_state(error=str(e))
        wake.wait(CFG.get('refresh_seconds', 60))
        wake.clear()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=os.path.join(HERE, 'web'), **k)

    def log_message(self, *a):
        pass

    def send_json(self, obj, code=200):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path == '/':
            self.path = '/display.dc.html'
        if self.path.startswith('/api/state'):
            with lock:
                return self.send_json(state)
        return super().do_GET()

    def do_POST(self):
        if self.path != '/api/toggle':
            return self.send_error(404)
        body = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or b'{}')
        try:
            graph('PATCH', '/me/todo/lists/%s/tasks/%s' % (q(body['listId']), q(body['id'])),
                  {'status': 'completed' if body['done'] else 'notStarted'})
            with lock:
                for t in state['tasks']:
                    if t['id'] == body['id']:
                        t['done'] = body['done']
            self.send_json({'ok': True})
            wake.set()
        except Exception as e:
            self.send_json({'ok': False, 'error': str(e)}, 500)


if __name__ == '__main__':
    if not CFG.get('client_id') or 'PASTE' in CFG['client_id']:
        raise SystemExit('Add your Application (client) ID to config.json first ♡')
    threading.Thread(target=poller, daemon=True).start()
    print('Pi To-Do running on http://localhost:8080')
    ThreadingHTTPServer(('127.0.0.1', 8080), Handler).serve_forever()
