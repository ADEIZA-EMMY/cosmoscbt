#!/usr/bin/env python
"""Simple smoke test: attempt admin and student login against local dev server."""
import time
import requests

BASE = 'http://127.0.0.1:5000'

def try_login(username, password):
    s = requests.Session()
    try:
        # Give server a moment
        time.sleep(2)
        r = s.post(f'{BASE}/login', data={'username': username, 'password': password}, allow_redirects=True, timeout=10)
        url = r.url
        status = r.status_code
        snippet = r.text[:400]
        success = False
        if url.endswith('/admin/dashboard') or url.endswith('/student/dashboard') or 'Login successful' in snippet:
            success = True
        return {'username': username, 'status': status, 'url': url, 'success': success, 'snippet': snippet}
    except Exception as e:
        return {'username': username, 'error': str(e)}

if __name__ == '__main__':
    tests = [
        ('Adeizaemma47', 'Adeizaemma47'),
        ('100001', '100001')
    ]
    for u,p in tests:
        res = try_login(u,p)
        print('---')
        if 'error' in res:
            print(f"{u} -> ERROR: {res['error']}")
        else:
            print(f"{u} -> status={res['status']} url={res['url']} success={res['success']}")
            print(res['snippet'])
