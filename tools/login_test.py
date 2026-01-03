import requests
s = requests.Session()
login_url='http://127.0.0.1:5000/login'
try:
    resp = s.post(login_url, data={'username':'admin','password':'admin123','user_type':'admin'}, allow_redirects=True, timeout=10)
    print('POST /login ->', resp.status_code, 'Final URL:', resp.url)
    print(resp.text[:800])
    r2 = s.get('http://127.0.0.1:5000/admin/dashboard', timeout=10)
    print('GET /admin/dashboard ->', r2.status_code, r2.url)
    print(r2.text[:800])
except Exception as e:
    print('ERROR', e)
