from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///cbt.db')
with engine.connect() as conn:
    conn.exec_driver_sql(
        """
        CREATE TABLE IF NOT EXISTS student_login (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            username VARCHAR(80) NOT NULL,
            source VARCHAR(20) NOT NULL DEFAULT 'self',
            created_by INTEGER,
            created_at DATETIME
        )
        """
    )
    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
    tables = [r[0] for r in res.fetchall()]
    print('Tables:', tables)
