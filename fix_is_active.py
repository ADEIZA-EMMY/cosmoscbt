#!/usr/bin/env python
"""Fix NULL is_active values in exams table"""
import os
import sys
from code1 import app, db

def fix_is_active():
    """Ensure all exams have is_active = true"""
    with app.app_context():
        try:
            # Update any NULL is_active to TRUE (legacy exams)
            result = db.session.execute(
                db.text("UPDATE exam SET is_active = true WHERE is_active IS NULL")
            )
            db.session.commit()
            rows_updated = result.rowcount
            print(f"✓ Fixed {rows_updated} exams with NULL is_active → TRUE")
            
            # Verify
            null_count = db.session.execute(
                db.text("SELECT COUNT(*) FROM exam WHERE is_active IS NULL")
            ).scalar()
            active_count = db.session.execute(
                db.text("SELECT COUNT(*) FROM exam WHERE is_active = true")
            ).scalar()
            print(f"✓ Exams with NULL is_active now: {null_count}")
            print(f"✓ Total active exams: {active_count}")
            
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            try:
                db.session.rollback()
            except:
                pass
            return False

if __name__ == '__main__':
    success = fix_is_active()
    sys.exit(0 if success else 1)
