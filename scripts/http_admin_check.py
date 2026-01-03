#!/usr/bin/env python
import requests
BASE='http://127.0.0.1:5000'
s = requests.Session()
try:
    r = s.post(f'{BASE}/login', data={'username':'Adeizaemma47','password':'Adeizaemma47'}, timeout=10)
    print('LOGIN status', r.status_code, 'url', r.url)
    r2 = s.get(f'{BASE}/admin/students', timeout=10)
    print('/admin/students status', r2.status_code)
    txt = r2.text
    if '100001' in txt:
        print('Found 100001 in admin students page')
    else:
        print('100001 not found in admin students page')
    # print snippet
    print(txt[:800])
except Exception as e:
    print('ERROR', e)
