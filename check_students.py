import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

from code1 import db, User, app

with app.app_context():
    students = User.query.filter_by(role='student').all()
    print(f'Total students: {len(students)}')
    global_students = [s for s in students if s.school_id is None]
    print(f'Global students: {len(global_students)}')
    for s in global_students[:10]:
        print(f'ID: {s.id}, Username: {s.username}, School: {s.school_id}')