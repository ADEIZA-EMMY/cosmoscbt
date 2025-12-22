import sqlite3, os
for p in ('cbt.db','instance/cbt.db','test.db'):
    ab = os.path.abspath(p)
    print('\nChecking', p, ab, 'exists=', os.path.exists(p))
    if os.path.exists(p):
        try:
            con = sqlite3.connect(p)
            cur = con.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t[0] for t in cur.fetchall()]
            print(' tables:', tables)
            if 'user' in tables:
                cur.execute("SELECT id,username,role,full_name FROM user LIMIT 10")
                print(' users:', cur.fetchall())
            con.close()
        except Exception as e:
            print(' error reading', p, e)
