from code1 import User, db
try:
    count = User.query.count()
    print(f'Total users: {count}')
    users = User.query.all()
    for u in users[:5]:
        print(f'  {u.id}: {u.username} (role={u.role}, school_id={u.school_id})')
except Exception as e:
    print(f'Error: {e}')
