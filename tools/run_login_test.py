import traceback

print('Starting login+create-exam test')
try:
    from code1 import app, db, User, Subject, Question, QuestionSet
except Exception:
    traceback.print_exc()
    raise SystemExit(1)

with app.app_context():
    client = app.test_client()
    try:
        resp = client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        print('\n== LOGIN RESPONSE ==')
        print('Status:', resp.status_code)
        print(resp.data.decode('utf-8', errors='replace')[:1000])
    except Exception:
        print('Login attempt raised exception:')
        traceback.print_exc()

    try:
        resp = client.get('/admin/exam/add')
        print('\n== GET /admin/exam/add ==')
        print('Status:', resp.status_code)
        snippet = resp.data.decode('utf-8', errors='replace')[:1200]
        print(snippet)
    except Exception:
        print('GET /admin/exam/add raised exception:')
        traceback.print_exc()

    try:
        subj = Subject.query.first()
        if not subj:
            print('No subject found; cannot create exam')
        else:
            data = {
                'subject_id': str(subj.id),
                'title': 'Auto Test Exam',
                'description': 'Created by automated test',
                'duration': '30',
                'subject_class': ''
            }
            resp = client.post('/admin/exam/add', data=data, follow_redirects=True)
            print('\n== POST create exam ==')
            print('Status:', resp.status_code)
            body = resp.data.decode('utf-8', errors='replace')
            print(body[:1200])
    except Exception:
        print('POST /admin/exam/add raised exception:')
        traceback.print_exc()

print('\nTest script finished')
