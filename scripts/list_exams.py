import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from code1 import app, db, Exam

with app.app_context():
    exams = Exam.query.limit(10).all()
    for e in exams:
        print(e.id, e.title, getattr(e,'code',None), 'active' if e.is_active else 'inactive', 'auto_start='+str(getattr(e,'auto_start_on_code',False)))
