from code1 import db, User, School, app

with app.app_context():
    # Get the first school as default
    default_school = School.query.first()
    if not default_school:
        print("No schools found, cannot assign school_id")
        exit(1)
    
    students = User.query.filter_by(role='student', school_id=None).all()
    print(f"Found {len(students)} students with no school_id")
    
    for student in students:
        student.school_id = default_school.id
        print(f"Assigned school_id {default_school.id} to student {student.username}")
    
    db.session.commit()
    print("Committed changes")