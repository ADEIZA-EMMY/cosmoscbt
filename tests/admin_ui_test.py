import requests
import time
import requests
import time
import os
from openpyxl import Workbook


def run_server_checks():
    BASE = 'http://127.0.0.1:5000'

    s = requests.Session()
    # wait for server
    for i in range(20):
        try:
            r = s.get(BASE, timeout=1)
            break
        except Exception:
            time.sleep(0.5)
    else:
        print('Server did not start in time')
        raise SystemExit(1)

    # Login as admin
    r = s.post(f"{BASE}/login", data={'username':'admin','password':'admin123'}, allow_redirects=True)
    print('Login status:', r.status_code)
    if 'Invalid' in r.text:
        print('Login failed: invalid credentials')

    # Check admin dashboard
    r = s.get(f"{BASE}/admin/dashboard")
    print('/admin/dashboard status:', r.status_code)
    print('dashboard contains upload link?', '/admin/question/upload' in r.text)

    # Check admin questions listing
    r = s.get(f"{BASE}/admin/questions")
    print('/admin/questions status:', r.status_code)

    # Check upload page
    r = s.get(f"{BASE}/admin/question/upload")
    print('/admin/question/upload status:', r.status_code)
    if 'Upload Questions' in r.text or 'Excel File' in r.text:
        print('Upload page looks correct')
    else:
        print('Upload page content preview:\n', r.text[:400])

    # Build a tiny Excel file to upload
    os.makedirs('uploads', exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.append(['Question','Option A','Option B','Correct Answer','Explanation','Mark'])
    ws.append(['What is 2+2?','4','3','A','Basic',1])
    fn = 'uploads/test_upload.xlsx'
    wb.save(fn)

    # Perform upload
    with open(fn, 'rb') as fh:
        files = {'file': ('test_upload.xlsx', fh, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        data = {'subject_id': '1'}
        r2 = s.post(f"{BASE}/admin/question/upload", files=files, data=data, allow_redirects=True)

    print('Upload POST status:', r2.status_code)
    if 'Saved' in r2.text or 'added' in r2.text or 'Upload' in r2.text or 'Question added successfully' in r2.text:
        print('Upload appears successful')
    else:
        print('Upload response length:', len(r2.text))
        print(r2.text[:1000])

    print('Done')


if __name__ == '__main__':
    run_server_checks()
                print('Upload appears successful')
