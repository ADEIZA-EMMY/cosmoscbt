#!/usr/bin/env python
import requests
from pprint import pprint
BASE='http://127.0.0.1:5000'
session = requests.Session()
print('Attempting superadmin login with Adeizaemma47/Adeizaemma47')
r = session.post(f'{BASE}/6869/login', data={'username':'Adeizaemma47','password':'Adeizaemma47'}, allow_redirects=True, timeout=10)
print('POST /6869/login ->', r.status_code, r.url)
if r.status_code!=200 and r.url.endswith('/6869'):
    print('Login likely redirected to dashboard')
print('Fetching /6869')
r2 = session.get(f'{BASE}/6869', timeout=10)
print('/6869 ->', r2.status_code)
# Now change password
newpw='NewSuper123!'
print('Changing password to', newpw)
r3 = session.post(f'{BASE}/6869/change_password', data={'current_password':'Adeizaemma47','new_password':newpw,'confirm_password':newpw}, allow_redirects=True, timeout=10)
print('POST /6869/change_password ->', r3.status_code, r3.url)
# Logout superadmin
session.get(f'{BASE}/6869/logout', timeout=5)
# Try login with old pwd (should fail)
s2 = requests.Session()
r_old = s2.post(f'{BASE}/6869/login', data={'username':'Adeizaemma47','password':'Adeizaemma47'}, allow_redirects=True, timeout=10)
print('Old password login attempt ->', r_old.status_code, r_old.url)
# Try login with new pwd
s3 = requests.Session()
r_new = s3.post(f'{BASE}/6869/login', data={'username':'Adeizaemma47','password':newpw}, allow_redirects=True, timeout=10)
print('New password login attempt ->', r_new.status_code, r_new.url)
if r_new.url.endswith('/6869') or 'Superadmin' in r_new.text:
    print('Superadmin password change verified successfully')
else:
    print('Superadmin change may have failed; check server logs or try manually')
