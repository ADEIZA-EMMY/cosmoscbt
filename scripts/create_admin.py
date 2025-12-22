import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code1 import app, db, User

with app.app_context():
    admin = User.query.filter_by(role='admin').first()
    if admin:
        print('Admin exists:', admin.username)
    else:
        print('No admin found — creating admin with username=admin password=admin123')
        u = User(username='admin', full_name='Administrator', role='admin')
        u.set_password('admin123')
        db.session.add(u)
        db.session.commit()
        print('Admin created')
