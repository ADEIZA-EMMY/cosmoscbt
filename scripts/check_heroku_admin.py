from code1 import app, User, School

def main():
    with app.app_context():
        u = User.query.filter_by(username='admin').first()
        if not u:
            print('NO_ADMIN')
        else:
            print('ADMIN:', u.username, 'id=', u.id, 'is_superadmin=', bool(getattr(u,'is_superadmin',False)), 'role=', u.role)
        schools = School.query.all()
        print('SCHOOLS_COUNT', len(schools))
        for s in schools:
            print('SCHOOL:', s.id, s.name, 'is_restricted=', getattr(s,'is_restricted',False))

if __name__ == '__main__':
    main()
