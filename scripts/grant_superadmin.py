#!/usr/bin/env python
"""Grant superadmin to the specified user (default: Adeizaemma47)."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from code1 import app, db, User

username = 'Adeizaemma47'
with app.app_context():
    u = User.query.filter_by(username=username).first()
    if not u:
        print(f'User {username} not found')
        sys.exit(1)
    u.is_superadmin = True
    db.session.commit()
    print(f'Marked {username} as superadmin (id={u.id})')
