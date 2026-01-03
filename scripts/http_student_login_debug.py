#!/usr/bin/env python
import requests
BASE='http://127.0.0.1:5000'
s = requests.Session()
try:
    r = s.post(f'{BASE}/login', data={'username':'100001','password':'100001'}, allow_redirects=True, timeout=10)
    print('POST /login ->', r.status_code, 'final url:', r.url)
    # print small snippet and look for flash messages
    text = r.text
    # Look for common flash messages inserted by the app
    for msg in ['Invalid username or password', 'Access denied', 'Account restricted', 'Student not found']:
        if msg in text:
            print('FOUND MESSAGE:', msg)
    snippet = text[:2000]
    print('SNIPPET:\n', snippet)
except Exception as e:
    print('ERROR', e)
