import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from code1 import app, db, User, School

PASSWORD = 'Adeizaemma47#'

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', full_name='Super Admin', role='admin')
        admin.set_password(PASSWORD)
        admin.is_superadmin = True
        db.session.add(admin)
        db.session.commit()
        print('Created admin user')
    else:
        admin.set_password(PASSWORD)
        admin.is_superadmin = True
        db.session.commit()
        print('Updated admin user password and promoted to superadmin')

    # Ensure school exists and associate admin if not set
    school = School.query.first()
    if school:
        if not admin.school_id:
            admin.school_id = school.id
            db.session.commit()
            print('Assigned admin to school', school.id)
    else:
        print('No school found — create one from /admin/schools or run scripts/add_school.py')

    print('Done')
