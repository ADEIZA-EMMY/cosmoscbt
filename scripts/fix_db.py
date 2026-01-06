from code1 import app, db
from sqlalchemy import text

with app.app_context():
    print('Ensuring DB tables...')
    db.create_all()
    conn = db.engine.connect()
    try:
        res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
        tables = [r[0] for r in res.fetchall()]
        print('Tables:', tables)
    finally:
        conn.close()
