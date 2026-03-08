#!/usr/bin/env python3
"""
Clear all student records and their related data from the database.
This script deletes:
- All student users (role='student')
- All exam sessions for students
- All answers related to student sessions
- All recordings for student sessions
"""

import sys
import os

# Add the project to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from code1 import app, db, User, ExamSession, Answer, Recording

def clear_all_students(force=False):
    """Delete all students and their related data."""
    with app.app_context():
        try:
            # Get all student users
            students = User.query.filter_by(role='student').all()
            student_count = len(students)
            student_ids = [s.id for s in students]
            
            print(f"\n📊 Found {student_count} students to delete")
            
            if student_count == 0:
                print("✅ No students to delete. Database is already clean.")
                return
            
            # Confirm deletion
            print("\n⚠️  This will delete:")
            print(f"   - {student_count} student accounts")
            
            # Count related records
            session_count = ExamSession.query.filter(ExamSession.student_id.in_(student_ids)).count()
            answer_count = Answer.query.join(ExamSession).filter(ExamSession.student_id.in_(student_ids)).count()
            recording_count = Recording.query.join(ExamSession).filter(ExamSession.student_id.in_(student_ids)).count()
            
            print(f"   - {session_count} exam sessions")
            print(f"   - {answer_count} exam answers")
            print(f"   - {recording_count} recordings")
            
            if not force:
                response = input("\n❓ Continue with deletion? (yes/no): ").strip().lower()
                if response not in ['yes', 'y']:
                    print("\n❌ Deletion cancelled.")
                    return
            else:
                print("\n✅ Auto-confirmed (--force flag)")
            
            # Delete recordings first
            if recording_count > 0:
                print(f"\n🗑️  Deleting {recording_count} recordings...")
                Recording.query.join(ExamSession).filter(ExamSession.student_id.in_(student_ids)).delete(synchronize_session=False)
                db.session.commit()
                print("✅ Recordings deleted")
            
            # Delete answers
            if answer_count > 0:
                print(f"🗑️  Deleting {answer_count} answers...")
                Answer.query.join(ExamSession).filter(ExamSession.student_id.in_(student_ids)).delete(synchronize_session=False)
                db.session.commit()
                print("✅ Answers deleted")
            
            # Delete exam sessions
            if session_count > 0:
                print(f"🗑️  Deleting {session_count} exam sessions...")
                ExamSession.query.filter(ExamSession.student_id.in_(student_ids)).delete(synchronize_session=False)
                db.session.commit()
                print("✅ Exam sessions deleted")
            
            # Delete student users
            print(f"🗑️  Deleting {student_count} student accounts...")
            for student in students:
                db.session.delete(student)
            db.session.commit()
            print("✅ Student accounts deleted")
            
            print("\n✨ All student data has been cleared successfully!")
            print(f"   - Deleted {student_count} students")
            print(f"   - Deleted {session_count} sessions")
            print(f"   - Deleted {answer_count} answers")
            print(f"   - Deleted {recording_count} recordings")
            print("\n🎉 Database is ready for new students!")
            
        except Exception as e:
            print(f"\n❌ Error during deletion: {e}")
            try:
                db.session.rollback()
            except:
                pass
            sys.exit(1)

if __name__ == '__main__':
    import sys
    # Check for --force flag to skip confirmation
    force = '--force' in sys.argv or '--yes' in sys.argv
    clear_all_students(force=force)
