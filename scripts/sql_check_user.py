#!/usr/bin/env python
import sqlite3, os
db = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'cbt.db'))
print('DB path:', db)
if not os.path.exists(db):
    print('DB file missing')
    raise SystemExit(1)

con = sqlite3.connect(db)
cur = con.cursor()
cur.execute("PRAGMA table_info(user)")
cols = cur.fetchall()
print('user table columns:')
for c in cols:
    print(' ', c)

cur.execute("SELECT id, username, role, full_name, temp_password FROM user WHERE username=?", ('100001',))
row = cur.fetchone()
if not row:
    print('user 100001 not found')
else:
    print('user row:', row)

con.close()
