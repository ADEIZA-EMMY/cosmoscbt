import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), '..', 'cbt.db')
DB = os.path.abspath(DB)
print('DB path:', DB)
conn = sqlite3.connect(DB)
c = conn.cursor()
cols = [r[1] for r in c.execute("PRAGMA table_info('exam')").fetchall()]
if 'allow_quick_start' not in cols:
    print('Adding allow_quick_start column to exam table')
    c.execute("ALTER TABLE exam ADD COLUMN allow_quick_start INTEGER DEFAULT 0")
    conn.commit()
    print('Added')
else:
    print('Column already present')
conn.close()
