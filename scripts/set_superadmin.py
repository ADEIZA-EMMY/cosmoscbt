#!/usr/bin/env python3
"""Set or update a superadmin user.

Usage:
  python scripts/set_superadmin.py --username USER --password PASS [--full-name NAME]

This script can be run locally or via `heroku run` on the deployed app to create/update
the superadmin account and preserve its password hash in the production database.
"""
import argparse

from code1 import app, db, User


def main():
    p = argparse.ArgumentParser(description='Create or update a superadmin user')
    p.add_argument('--username', required=True, help='Superadmin username')
    p.add_argument('--password', required=True, help='Superadmin password')
    p.add_argument('--full-name', default='Super Admin', help='Full name (optional)')
    args = p.parse_args()

    with app.app_context():
        u = User.query.filter_by(username=args.username).first()
        if not u:
            u = User(username=args.username, full_name=args.full_name, role='admin')
            u.set_password(args.password)
            u.is_superadmin = True
            db.session.add(u)
            db.session.commit()
            print('Created superadmin:', u.id, u.username)
        else:
            u.set_password(args.password)
            u.full_name = args.full_name
            u.role = 'admin'
            u.is_superadmin = True
            db.session.commit()
            print('Updated superadmin:', u.id, u.username)


if __name__ == '__main__':
    main()
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from code1 import app, db, User

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        print('admin user not found')
    else:
        admin.is_superadmin = True
        db.session.commit()
        print('Marked admin as superadmin')
