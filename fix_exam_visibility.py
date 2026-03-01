#!/usr/bin/env python
"""Fix NULL is_active values and ensure exam visibility"""
import os
from code1 import app, db

def fix_exam_visibility():
    """Ensure all exams have is_active = true"""
    with app.app_context():
        try:
            # Update any NULL is_active to TRUE (legacy exams)
            result = db.session.execute(
                db.text("UPDATE exam SET is_active = true WHERE is_active IS NULL")
            )
            db.session.commit()
            print(f"✓ Fixed {result.rowcount} exams with NULL is_active → TRUE")
            
            # Verify
            null_count = db.session.execute(
                db.text("SELECT COUNT(*) FROM exam WHERE is_active IS NULL")
            ).scalar()
            print(f"✓ Exams with NULL is_active now: {null_count}")
            
            # Show some exam data
            exams = db.session.execute(
                db.text("SELECT id, title, is_active, school_id FROM exam LIMIT 5")
            ).fetchall()
            print("\nSample exams after fix:")
            for e in exams:
                print(f"  - {e[1]}: is_active={e[2]}, school_id={e[3]}")
            
            print("\n✓ Exam visibility fix completed successfully")
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            try:
                db.session.rollback()
            except:
                pass
            return False

if __name__ == '__main__':
    fix_exam_visibility()
