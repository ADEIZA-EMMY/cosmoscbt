#!/usr/bin/env python
"""Reset a student's password directly in the instance sqlite DB.
Usage: python scripts/reset_student_password.py 100001 newpass
If no args provided, defaults to 100001 / 100001.
"""
import sys, os
from werkzeug.security import generate_password_hash

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance', 'cbt.db'))
if len(sys.argv) >= 2:
    username = sys.argv[1]
else:
    username = '100001'
if len(sys.argv) >= 3:
    newpw = sys.argv[2]
else:
    newpw = username

if not os.path.exists(db_path):
    print('DB not found at', db_path)
    sys.exit(1)

conn = None
try:
    import sqlite3
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('SELECT id, username FROM user WHERE username=?', (username,))
    row = cur.fetchone()
    if not row:
        print('User not found:', username)
        sys.exit(1)
    uid = row[0]
    pw_hash = generate_password_hash(newpw)
    # Update password_hash and temp_password
    cur.execute('UPDATE user SET password_hash=?, temp_password=? WHERE id=?', (pw_hash, newpw, uid))
    conn.commit()
    print(f'Updated password for {username} (id={uid}). Temp password stored.')
except Exception as e:
    print('Error:', e)
    sys.exit(2)
finally:
    if conn:
        conn.close()
