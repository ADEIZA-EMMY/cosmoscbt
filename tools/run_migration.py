"""One-time migration script to ensure QuestionSet table exists and
adds `question_set_id` to `question` table if missing.

Run with the project's virtualenv python.
"""
import os
import sqlite3
from code1 import app, db

def run_migration():
    with app.app_context():
        # Ensure tables for new models (QuestionSet) are created
        db.create_all()
        # Resolve SQLite DB path from engine URL or config
        engine_url = str(db.engine.url)
        db_path = None
        if engine_url.startswith('sqlite:///'):
            db_path = engine_url.replace('sqlite:///', '')
        else:
            # fallback to instance/cbt.db
            db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'cbt.db')
            db_path = os.path.abspath(db_path)
        print('Using DB path:', db_path)
        if not os.path.exists(db_path):
            raise SystemExit(f'Database file not found: {db_path}')
        conn = sqlite3.connect(db_path)
        try:
            cur = conn.execute("PRAGMA table_info('question')")
            cols = [r[1] for r in cur.fetchall()]
            if 'question_set_id' not in cols:
                print('Adding question_set_id column to question table...')
                conn.execute('ALTER TABLE question ADD COLUMN question_set_id INTEGER')
                conn.commit()
                print('Added question_set_id')
            else:
                print('question_set_id already present')
        finally:
            conn.close()

if __name__ == '__main__':
    run_migration()
    print('Migration finished')
