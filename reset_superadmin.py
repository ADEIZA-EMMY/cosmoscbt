# reset_superadmin.py
from getpass import getpass
from code1 import app, db, User

def main():
    with app.app_context():
        u = User.query.filter_by(is_superadmin=True).first()
        if not u:
            print("No superadmin user found.")
            return
        p1 = getpass("New password: ")
        p2 = getpass("Confirm password: ")
        if p1 != p2:
            print("Passwords do not match.")
            return
        u.set_password(p1)
        db.session.commit()
        print("Superadmin password updated for:", u.username)

if __name__ == "__main__":
    main()