import sqlite3

conn = sqlite3.connect('instance/cbt.db')
cursor = conn.cursor()

print("=" * 60)
print("DETAILED DIAGNOSIS")
print("=" * 60)

# Admin users
print("\n1. ADMIN USERS:")
cursor.execute("SELECT id, username, full_name, school_id, is_superadmin FROM user WHERE role='admin'")
for admin_id, username, full_name, school_id, is_superadmin in cursor.fetchall():
    superadmin_flag = " (SUPERADMIN)" if is_superadmin else ""
    school_info = f"school_id={school_id}" if school_id else "school_id=NULL"
    print(f"   admin_id={admin_id}, username={username}, full_name={full_name}")
    print(f"   {school_info}{superadmin_flag}")

# Students by school_id
print("\n2. STUDENTS BY SCHOOL_ID:")
cursor.execute("SELECT school_id, COUNT(*) FROM user WHERE role='student' GROUP BY school_id")
for school_id, count in cursor.fetchall():
    school_info = f"school_id={school_id}" if school_id else "school_id=NULL"
    print(f"   {school_info}: {count} students")

# Schools
print("\n3. SCHOOLS:")
cursor.execute("SELECT id, name FROM school")
schools = cursor.fetchall()
if schools:
    for school_id, name in schools:
        print(f"   school_id={school_id}, name={name}")
else:
    print("   [NO SCHOOLS FOUND]")

# Sample students
print("\n4. SAMPLE STUDENTS (first 5):")
cursor.execute("SELECT username, full_name, student_class, school_id FROM user WHERE role='student' LIMIT 5")
for username, full_name, student_class, school_id in cursor.fetchall():
    school_info = f"school_id={school_id}" if school_id else "school_id=NULL"
    print(f"   {username}: {full_name}, class={student_class}, {school_info}")

# Analysis
print("\n5. ROOT CAUSE ANALYSIS:")
cursor.execute("SELECT COUNT(*) FROM user WHERE role='admin' AND is_superadmin=0 AND school_id IS NULL")
admins_without_school = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM user WHERE role='student'")
total_students = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM user WHERE role='student' AND school_id IS NULL")
null_school_students = cursor.fetchone()[0]

print(f"   - Total students: {total_students}")
print(f"   - Students with school_id=NULL: {null_school_students}")
print(f"   - Regular admin users without school_id: {admins_without_school}")

if admins_without_school > 0 and total_students > 0:
    print(f"\n   ⚠️  FOUND THE PROBLEM!")
    print(f"   The regular admin(s) cannot see students because:")
    print(f"   1. Admin user(s) have NO school_id assigned")
    print(f"   2. When admin logs in, _get_effective_school_id() returns None")
    print(f"   3. students_for_current_user() returns empty list when school_id is None")
    print(f"\n   FIX: Assign a school_id to the admin user(s), or make sure")
    print(f"   students have the same school_id as the admin")
elif null_school_students == total_students and admins_without_school > 0:
    print(f"\n   ⚠️  PARTIAL MATCH:")
    print(f"   All students have school_id=NULL but admin doesn't match")
    print(f"   This could be the issue - students need matching school_id or")
    print(f"   admin needs to be superadmin")

conn.close()
