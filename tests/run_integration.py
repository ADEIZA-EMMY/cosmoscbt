import sys
import os
# Ensure project root is on sys.path so code1 can be imported when running from tests/ directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from code1 import app, init_db

# Simple integration checks using Flask test client
if __name__ == '__main__':
    print('Initializing DB...')
    try:
        init_db()
    except Exception as e:
        print('init_db error:', e)

    app.testing = True
    client = app.test_client()

    print('1) GET /login')
    r = client.get('/login')
    print('  status', r.status_code)

    print('2) POST /login (student)')
    data = {'username': '100001', 'password': '100001'}
    r = client.post('/login', data=data, follow_redirects=True)
    print('  status', r.status_code)
    print('  redirected to', r.request.path)

    print('3) Access /student/dashboard')
    r = client.get('/student/dashboard')
    print('  status', r.status_code)

    print('4) Access /admin/questions (should redirect without admin login)')
    r = client.get('/admin/questions', follow_redirects=False)
    print('  status', r.status_code)

    print('5) GET /admin/question/upload (should redirect without admin)')
    r = client.get('/admin/question/upload')
    print('  status', r.status_code)

    print('6) GET /student/exam/1 (requires login)')
    r = client.get('/student/exam/1')
    print('  status', r.status_code)

    print('Done')
