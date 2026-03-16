from code1 import db, User, app

with app.app_context():
    student = User.query.filter_by(username='teststudent').first()
    if student:
        print(f"Deleting student {student.username}")
        db.session.delete(student)
        db.session.commit()
        print("Deleted")
    else:
        print("Student not found")