import requests
import uuid

base = 'https://cosmoscbtapp.herokuapp.com'
register_url = f'{base}/register'
login_url = f'{base}/login'
dash_url = f'{base}/student/dashboard'

s = requests.Session()
username = f'testuser_{uuid.uuid4().hex[:8]}'
password = 'TestPass123!'
print('Testing with', username)

# Register
r = s.post(register_url, data={'username': username, 'password': password, 'full_name': 'Smoke Test'}, allow_redirects=True, timeout=30)
print('Register status:', r.status_code, 'final url:', r.url)
print('Register response snippet:', r.text[:200].replace('\n',' '))

# Login
r = s.post(login_url, data={'username': username, 'password': password}, allow_redirects=True, timeout=30)
print('Login status:', r.status_code, 'final url:', r.url)
print('Login response snippet:', r.text[:200].replace('\n',' '))

# Access dashboard
r = s.get(dash_url, allow_redirects=True, timeout=30)
print('Dashboard status:', r.status_code, 'final url:', r.url)
print('Dashboard response snippet:', r.text[:400].replace('\n',' '))

# Basic assertions
if r.status_code == 200 and 'Access denied' not in r.text and 'Login' not in r.url:
    print('SMOKE TEST: PASS')
else:
    print('SMOKE TEST: FAIL')
