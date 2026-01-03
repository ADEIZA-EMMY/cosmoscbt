import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code1 import app, db
from sqlalchemy import text

with app.app_context():
    with db.engine.connect() as conn:
        res = conn.execute(text("PRAGMA table_info('exam')"))
        cols = [r[1] for r in res]
        if 'allow_quick_start' not in cols:
            print('Adding allow_quick_start column')
            conn.execute(text("ALTER TABLE exam ADD COLUMN allow_quick_start INTEGER DEFAULT 0"))
            print('Added')
        else:
            print('allow_quick_start column already present')

        # Add auto_start_on_code column if missing
        if 'auto_start_on_code' not in cols:
            print('Adding auto_start_on_code column')
            conn.execute(text("ALTER TABLE exam ADD COLUMN auto_start_on_code INTEGER DEFAULT 0"))
            print('Added auto_start_on_code')
        else:
            print('auto_start_on_code column already present')
        # Add temp_password to user table if missing
        res_user = conn.execute(text("PRAGMA table_info('user')"))
        user_cols = [r[1] for r in res_user]
        if 'temp_password' not in user_cols:
            print('Adding temp_password to user table')
            conn.execute(text("ALTER TABLE user ADD COLUMN temp_password TEXT"))
            print('Added temp_password')
        else:
            print('temp_password already present')
        # Add is_superadmin and is_restricted columns to user table if missing
        res_user = conn.execute(text("PRAGMA table_info('user')"))
        user_cols = [r[1] for r in res_user]
        if 'is_superadmin' not in user_cols:
            print('Adding is_superadmin to user table')
            conn.execute(text("ALTER TABLE user ADD COLUMN is_superadmin INTEGER DEFAULT 0"))
            print('Added is_superadmin')
        else:
            print('is_superadmin already present')

        if 'is_restricted' not in user_cols:
            print('Adding is_restricted to user table')
            conn.execute(text("ALTER TABLE user ADD COLUMN is_restricted INTEGER DEFAULT 0"))
            print('Added is_restricted')
        else:
            print('is_restricted already present')
        # Add is_restricted column to user table if missing
        if 'is_restricted' not in user_cols:
            print('Adding is_restricted to user table')
            conn.execute(text("ALTER TABLE user ADD COLUMN is_restricted INTEGER DEFAULT 0"))
            print('Added is_restricted')
        else:
            print('is_restricted already present')
