import sys, os, importlib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
code1 = importlib.import_module('code1')
app = getattr(code1, 'app', None)
if not app:
    raise RuntimeError('Could not load app from code1')
with app.test_client() as c:
    resp = c.post('/login', data={'username':'admin','password':'admin123'}, follow_redirects=True)
    print('POST /login ->', resp.status_code)
    data = resp.data.decode('utf-8', errors='replace')
    for line in data.splitlines()[:30]:
        print(line)
