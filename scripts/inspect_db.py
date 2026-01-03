import sqlite3
conn = sqlite3.connect('cbt.db')
cur = conn.cursor()
try:
    cur.execute("PRAGMA table_info('subject')")
    rows = cur.fetchall()
    print('subject table columns:')
    for r in rows:
        print(r)
except Exception as e:
    print('error:', e)
finally:
    conn.close()
