import sys, os, random
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from code1 import app, db, Exam, User, ExamAccessCode

with app.app_context():
    exam = Exam.query.filter_by(id=2).first()
    user = User.query.filter_by(username='tempuser1').first()
    if not exam or not user:
        print('Exam or user not found')
    else:
        code = str(random.randint(100000,999999))
        eac = ExamAccessCode(exam_id=exam.id, student_id=user.id, code=code)
        db.session.add(eac)
        db.session.commit()
        print('Created access code', code)
