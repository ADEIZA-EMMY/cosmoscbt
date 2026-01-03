# One-off script to backfill missing exam codes
from code1 import app, db, Exam, generate_unique_exam_code
from sqlalchemy import text

with app.app_context():
    # Ensure `code` column exists in the `exam` table; add if missing (SQLite)
    try:
        res = db.session.execute(text("PRAGMA table_info('exam')"))
        cols = [row[1] for row in res]
    except Exception:
        cols = []

    if 'code' not in cols:
        try:
            db.session.execute(text("ALTER TABLE exam ADD COLUMN code VARCHAR(6)"))
            db.session.commit()
            print('Added `code` column to exam table')
        except Exception as e:
            db.session.rollback()
            print('Failed to add code column:', e)

    exams = Exam.query.filter((Exam.code == None) | (Exam.code == '')).all()
    if not exams:
        print('No exams without codes found.')
    else:
        assigned = 0
        for ex in exams:
            code = generate_unique_exam_code()
            ex.code = code
            db.session.add(ex)
            assigned += 1
        db.session.commit()
        print(f'Assigned codes to {assigned} exams.')
