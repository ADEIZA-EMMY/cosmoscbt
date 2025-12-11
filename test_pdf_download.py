#!/usr/bin/env python
import requests, re

BASE = 'http://127.0.0.1:5000'
s = requests.Session()
# Login as student
r = s.post(f'{BASE}/login', data={'username':'100001','password':'100001','user_type':'student'})
print('Login', r.status_code)
# find a result session id
r = s.get(f'{BASE}/student/results')
m = re.search(r'/student/result/(\d+)', r.text)
if not m:
    print('No session id found on results page')
    exit(1)
sid = m.group(1)
print('Using session id', sid)
# request pdf
r = s.get(f'{BASE}/student/result/{sid}/pdf')
print('Status:', r.status_code)
ct = r.headers.get('Content-Type', '')
cd = r.headers.get('Content-Disposition', '')
print('Content-Type:', ct)
print('Content-Disposition:', cd)
# Save file
fname = f'result_{sid}.pdf' if 'pdf' in ct else f'result_{sid}.html'
with open(fname, 'wb') as f:
    f.write(r.content)
print('Saved to', fname)
