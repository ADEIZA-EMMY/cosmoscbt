#!/usr/bin/env python
"""
Migration: Add question_set_id column to exam table
"""
import os
import sys
from sqlalchemy import text

def main():
    # Import app after setting up path
    from code1 import app, db
    
    with app.app_context():
        try:
            conn = db.engine.connect()
            
            # List of ALTER TABLE statements to run
            migrations = [
                # Exam table columns
                'ALTER TABLE exam ADD COLUMN IF NOT EXISTS question_set_id INTEGER',
                'ALTER TABLE exam ADD COLUMN IF NOT EXISTS school_id INTEGER',
                'ALTER TABLE exam ADD COLUMN IF NOT EXISTS school_code VARCHAR(50)',
                'ALTER TABLE exam ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true',
                
                # Question table columns
                'ALTER TABLE question ADD COLUMN IF NOT EXISTS question_set_id INTEGER',
                'ALTER TABLE question ADD COLUMN IF NOT EXISTS subject_class VARCHAR(50)',
                'ALTER TABLE question ADD COLUMN IF NOT EXISTS question_image VARCHAR(200)',
                'ALTER TABLE question ADD COLUMN IF NOT EXISTS is_theory BOOLEAN DEFAULT false',
                'ALTER TABLE question ADD COLUMN IF NOT EXISTS theory_text TEXT',
                
                # User table columns
                'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS school_id INTEGER',
                'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS student_class VARCHAR(50)',
                'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS passport_filename VARCHAR(200)',
                'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS gender VARCHAR(20)',
                'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS is_superadmin BOOLEAN DEFAULT false',
                'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS is_restricted BOOLEAN DEFAULT false',
                'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS temp_password VARCHAR(200)',
                
                # Subject table columns
                'ALTER TABLE subject ADD COLUMN IF NOT EXISTS code VARCHAR(20)',
                'ALTER TABLE subject ADD COLUMN IF NOT EXISTS subject_class VARCHAR(50)',
                
                # School table columns
                'ALTER TABLE school ADD COLUMN IF NOT EXISTS access_code VARCHAR(10)',
                'ALTER TABLE school ADD COLUMN IF NOT EXISTS is_restricted BOOLEAN DEFAULT false',
            ]
            
            for sql in migrations:
                try:
                    print(f'Running: {sql}')
                    conn.execute(text(sql))
                    conn.commit()
                    print(f'  ✓ Success')
                except Exception as e:
                    print(f'  ⚠ Error (may already exist): {str(e)[:80]}')
                    try:
                        conn.rollback()
                    except:
                        pass
            
            conn.close()
            print('\n✓ All migrations completed successfully')
            return 0
            
        except Exception as e:
            print(f'\n✗ Migration failed: {str(e)}')
            import traceback
            traceback.print_exc()
            return 1

if __name__ == '__main__':
    sys.exit(main())
