import runpy, sys, os

# ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
mod = runpy.run_path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'code1.py')))
app = mod.get('app')
if not app:
    raise RuntimeError('Could not load app from code1.py')

endpoints = ['/', '/login', '/start', '/admin/exam/add', '/admin/question/upload', '/admin/question/template_theory']
with app.test_client() as c:
    for e in endpoints:
        resp = c.get(e)
        print(e, resp.status_code)
        try:
            print(resp.data[:400].decode('utf-8',errors='replace').splitlines()[:6])
        except Exception:
            pass
