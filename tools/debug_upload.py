import sys
import os
import traceback

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from code1 import app

print('Starting Flask test client debug for /admin/question/upload')

try:
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'admin'
    resp = client.get('/admin/question/upload')
    print('Status code:', resp.status_code)
    data = resp.get_data(as_text=True)
    print('Response length:', len(data))
    print(data[:800])
except Exception:
    print('Exception during test client request:')
    traceback.print_exc()
