#!/usr/bin/env python
"""Create admin user Adeizaemma47 with password Adeizaemma47."""
import sys
import os
# Ensure project root is on sys.path so we can import code1
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)
try:
    from code1 import app, db, User
except Exception as e:
    print('Failed importing app modules:', e)
    sys.exit(1)

with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print('db.create_all() failed:', e)

    username = 'Adeizaemma47'
    password = 'Adeizaemma47'
    try:
        user = User.query.filter_by(username=username).first()
        if user:
            print(f'User {username} already exists (id={user.id})')
            sys.exit(0)
        user = User(username=username, role='admin', full_name='Adeiza Emma')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f'Created admin user {username} (id={user.id})')
    except Exception as e:
        print('Error creating user:', e)
        sys.exit(2)
