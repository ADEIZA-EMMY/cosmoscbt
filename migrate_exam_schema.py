#!/usr/bin/env python
"""
Migration script to add missing columns to exam table
"""

from code1 import app, db
import sqlalchemy
from sqlalchemy import text

def migrate_exam_schema():
    with app.app_context():
        try:
            # Create all tables first
            db.create_all()
            print('✓ Tables created/verified')
            
            # Get database connection
            conn = db.engine.connect()
            
            # Add missing columns to exam table (using IF NOT EXISTS for idempotency)
            columns_to_add = [
                ('school_id', 'INTEGER'),
                ('school_code', "VARCHAR(50)"),
                ('is_active', "BOOLEAN DEFAULT true"),
                ('question_set_id', 'INTEGER'),
            ]
            
            for col_name, col_type in columns_to_add:
                try:
                    sql = f"ALTER TABLE exam ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
                    conn.execute(text(sql))
                    print(f'✓ Added column: exam.{col_name}')
                except Exception as e:
                    print(f'⚠ Could not add exam.{col_name}: {str(e)[:80]}')
            
            # Commit all changes
            conn.commit()
            conn.close()
            
            print('✓ Exam schema migration complete')
            return True
            
        except Exception as e:
            print(f'✗ Migration failed: {str(e)}')
            return False

if __name__ == '__main__':
    success = migrate_exam_schema()
    exit(0 if success else 1)
