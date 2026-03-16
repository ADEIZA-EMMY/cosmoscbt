from code1 import db, User, School, app

with app.app_context():
    # Create a test student with no school_id
    test_student = User(username='teststudent', full_name='Test Student', role='student')
    test_student.set_password('password')
    test_student.student_class = 'JSS1'
    # Don't set school_id to simulate global student
    db.session.add(test_student)
    db.session.commit()
    print(f"Created test student with id {test_student.id}, school_id {test_student.school_id}")