import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from code1 import app, db, User

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        print('admin user not found')
    else:
        admin.is_superadmin = True
        db.session.commit()
        print('Marked admin as superadmin')
