import os
import sys
# ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from code1 import app, db, User
from datetime import datetime

app.testing = True
client = app.test_client()

# choose a unique username
username = 'testuser_' + datetime.utcnow().strftime('%Y%m%d%H%M%S')

data = {
    'username': username,
    'password': 'Password123!',
    'full_name': 'Test User',
    'student_class': 'SS1',
    'gender': 'Male'
}

resp = client.post('/register', data=data, follow_redirects=True)
print('STATUS', resp.status_code)
body = resp.get_data(as_text=True)
print('BODY SNIPPET:\n', body[:800])

# confirm user in DB
with app.app_context():
    u = User.query.filter_by(username=username).first()
    print('DB USER:', bool(u), u.username if u else None)
