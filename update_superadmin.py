#!/usr/bin/env python
"""Create or update superadmin credentials in PostgreSQL database."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from code1 import app, db, User

if __name__ == '__main__':
    with app.app_context():
        try:
            # Try to find existing admin user
            admin = User.query.filter_by(username='admin').first()
            
            if not admin:
                # Create new superadmin
                admin = User(
                    username='Adeizaemma47',
                    role='admin',
                    full_name='Adeizaemma47'
                )
                admin.set_password('Adeizaemma47')
                admin.is_superadmin = True
                db.session.add(admin)
                db.session.commit()
                print('✓ Superadmin created successfully!')
            else:
                # Update existing admin user
                admin.username = 'Adeizaemma47'
                admin.set_password('Adeizaemma47')
                admin.is_superadmin = True
                db.session.commit()
                print('✓ Superadmin updated successfully!')
            
            print('✓ Username: Adeizaemma47')
            print('✓ Password: Adeizaemma47')
            print('✓ Ready to login!')
                
        except Exception as e:
            print(f'✗ Error: {e}')
            import traceback
            traceback.print_exc()
            sys.exit(1)
