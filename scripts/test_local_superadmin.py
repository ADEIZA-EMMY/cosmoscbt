import os, sys
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from code1 import app, db, User

PASSWORD = 'Adeizaemma47#'

def main():
    with app.app_context():
        # Ensure tables exist
        try:
            db.create_all()
        except Exception:
            try:
                db.session.rollback()
            except Exception:
                pass

        # Create or update admin
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', full_name='Super Admin', role='admin')
            admin.set_password(PASSWORD)
            admin.is_superadmin = True
            db.session.add(admin)
            db.session.commit()
            print('Created local admin user with requested password')
        else:
            admin.set_password(PASSWORD)
            admin.is_superadmin = True
            db.session.commit()
            print('Updated local admin user password and ensured superadmin flag')

        # Verify password check
        ok = admin.check_password(PASSWORD)
        print('Password verification for admin:', ok)

if __name__ == '__main__':
    main()
