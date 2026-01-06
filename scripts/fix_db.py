from code1 import db
from sqlalchemy import text

print('DB URI:', db.engine.url)
conn = db.engine.connect()
try:
    db.create_all()
    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
    tables = [r[0] for r in res.fetchall()]
    print('Tables:', tables)
finally:
    conn.close()
