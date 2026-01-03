#!/usr/bin/env python
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from code1 import app, User

with app.app_context():
    for uname in ('Adeizaemma47','100001'):
        u = User.query.filter_by(username=uname).first()
        if not u:
            print(f'{uname}: NOT FOUND')
            continue
        print(f'{uname}: id={u.id} role={u.role} full_name={u.full_name} temp_password={getattr(u,"temp_password",None)}')
        try:
            print(f'  check_password("{uname}") ->', u.check_password(uname))
        except Exception as e:
            print('  check_password error', e)
