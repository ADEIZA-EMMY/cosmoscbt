#!/usr/bin/env python3
"""Verify that all students have been cleared from the database."""

import sys
import os
import codecs

# Force UTF-8 output encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from code1 import app, db, User

def verify_students_cleared():
    """Check how many students are in the database."""
    with app.app_context():
        try:
            student_count = User.query.filter_by(role='student').count()
            total_users = User.query.count()
            
            print("\n" + "="*50)
            print("[DATABASE VERIFICATION REPORT]")
            print("="*50)
            print(f"\n✓ Total users in database: {total_users}")
            print(f"  Student accounts remaining: {student_count}")
            
            if student_count == 0:
                print("\n✓ SUCCESS! All students have been cleared!")
                print("✓ Database is ready for adding new students.")
                return True
            else:
                print(f"\n✗ WARNING: {student_count} students still in database")
                print("  Run: python clear_all_students.py --force")
                return False
                
        except Exception as e:
            print(f"\n✗ Error: {e}")
            return False

if __name__ == '__main__':
    success = verify_students_cleared()
    sys.exit(0 if success else 1)
