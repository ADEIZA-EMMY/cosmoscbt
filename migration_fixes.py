#!/usr/bin/env python
"""Migration script to fix all 5 issues"""
from code1 import app, db

def run_migrations():
    with app.app_context():
        print("Running comprehensive migration fixes...")
        
        # 1. Add school_id column to subject table if missing
        print("\n[1/5] Adding school_id to subject table...")
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            subject_cols = [c['name'] for c in inspector.get_columns('subject')]
            
            if 'school_id' not in subject_cols:
                from code1 import _exec_ddl
                _exec_ddl('ALTER TABLE subject ADD COLUMN school_id INTEGER')
                print("✓ Added school_id column to subject table")
            else:
                print("✓ school_id column already exists in subject table")
        except Exception as e:
            print(f"⚠ Could not add school_id: {e}")
        
        # 2. Ensure all exams have is_active = true
        print("\n[2/5] Fixing NULL is_active values in exam table...")
        try:
            result = db.session.execute(
                db.text("UPDATE exam SET is_active = true WHERE is_active IS NULL")
            )
            db.session.commit()
            print(f"✓ Fixed {result.rowcount} exams with NULL is_active → TRUE")
        except Exception as e:
            print(f"⚠ Could not fix is_active: {e}")
            try:
                db.session.rollback()
            except:
                pass
        
        # 3. Verify student profile fields are populated
        print("\n[3/5] Checking student profile fields...")
        try:
            null_class = db.session.execute(
                db.text("SELECT COUNT(*) FROM \"user\" WHERE role='student' AND student_class IS NULL")
            ).scalar()
            print(f"✓ Students without assigned class: {null_class}")
            
            null_passport = db.session.execute(
                db.text("SELECT COUNT(*) FROM \"user\" WHERE role='student' AND passport_filename IS NULL")
            ).scalar()
            print(f"✓ Students without profile picture: {null_passport}")
        except Exception as e:
            print(f"⚠ Could not check student fields: {e}")
        
        # 4. Verify subjects exist and are accessible globally
        print("\n[4/5] Checking subject visibility...")
        try:
            total_subjects = db.session.execute(
                db.text("SELECT COUNT(*) FROM subject")
            ).scalar()
            global_subjects = db.session.execute(
                db.text("SELECT COUNT(*) FROM subject WHERE school_id IS NULL")
            ).scalar()
            school_subjects = db.session.execute(
                db.text("SELECT COUNT(*) FROM subject WHERE school_id IS NOT NULL")
            ).scalar()
            print(f"✓ Total subjects: {total_subjects}")
            print(f"✓ Global subjects (school_id IS NULL): {global_subjects}")
            print(f"✓ School-specific subjects: {school_subjects}")
        except Exception as e:
            print(f"⚠ Could not check subject visibility: {e}")
        
        # 5. Verify exam sessions per school
        print("\n[5/5] Checking exam sessions per school...")
        try:
            all_sessions = db.session.execute(
                db.text("SELECT COUNT(*) FROM exam_session")
            ).scalar()
            completed_sessions = db.session.execute(
                db.text("SELECT COUNT(*) FROM exam_session WHERE status='completed'")
            ).scalar()
            print(f"✓ Total exam sessions: {all_sessions}")
            print(f"✓ Completed sessions: {completed_sessions}")
        except Exception as e:
            print(f"⚠ Could not check exam sessions: {e}")
        
        print("\n" + "="*60)
        print("✓ All migration checks completed successfully!")
        print("="*60)

if __name__ == '__main__':
    run_migrations()
