import requests
from bs4 import BeautifulSoup

BASE = 'https://cosmoscbtapp-ed1785342c7c.herokuapp.com'
s = requests.Session()

def check(path):
    try:
        r = s.get(BASE+path, timeout=15)
        print(path, r.status_code)
        return r
    except Exception as e:
        print('ERR', path, e)
        return None

print('GET /')
check('/')

print('\nLogin admin...')
resp = s.post(BASE+'/login', data={'username':'admin','password':'admin123'})
print('POST /login ->', resp.status_code, resp.url)

# Access admin dashboard
print('\nGET /admin/dashboard')
resp = check('/admin/dashboard')

# Find an exam id from /admin/exams page
print('\nGET /admin/exams')
resp = check('/admin/exams')
if resp and resp.status_code==200:
    soup = BeautifulSoup(resp.text, 'html.parser')
    link = soup.find('a', href=True, text=lambda t: t and 'Exam' in t)
    # fallback: find first exam detail link
    a = soup.find('a', href=True)
    if a:
        href = a['href']
        print('Found link', href)
        check(href)

print('\nDone')
