from code1 import db
from sqlalchemy import inspect, text

inspector = inspect(db.engine)
if 'exam' not in inspector.get_table_names():
    print('No exam table present, aborting')
    exit(1)

cols = [c['name'] for c in inspector.get_columns('exam')]
print('Current exam columns:', cols)

added = []
if 'school_id' not in cols:
    try:
        db.session.execute(text('ALTER TABLE exam ADD COLUMN school_id INTEGER'))
        db.session.commit()
        added.append('school_id')
        print('Added school_id')
    except Exception as e:
        db.session.rollback()
        print('Failed to add school_id:', e)
if 'school_code' not in cols:
    try:
        db.session.execute(text('ALTER TABLE exam ADD COLUMN school_code VARCHAR(50)'))
        db.session.commit()
        added.append('school_code')
        print('Added school_code')
    except Exception as e:
        db.session.rollback()
        print('Failed to add school_code:', e)
if 'is_active' not in cols:
    try:
        db.session.execute(text('ALTER TABLE exam ADD COLUMN is_active BOOLEAN DEFAULT true'))
        db.session.commit()
        added.append('is_active')
        print('Added is_active')
    except Exception as e:
        db.session.rollback()
        print('Failed to add is_active:', e)

cols_after = [c['name'] for c in inspector.get_columns('exam')]
print('Final exam columns:', cols_after)
print('Added columns:', added)
