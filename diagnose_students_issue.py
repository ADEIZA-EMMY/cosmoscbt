#!/usr/bin/env python3
"""Diagnose why students are not showing in the admin portal."""

import sys
sys.path.insert(0, '.')

from code1 import app, db, User, School

def diagnose():
    with app.app_context():
        print("=" * 60)
        print("STUDENT VISIBILITY DIAGNOSIS")
        print("=" * 60)
        
        # Check Schools
        print("\n1. SCHOOLS IN DATABASE:")
        schools = School.query.all()
        for school in schools:
            print(f"   - ID {school.id}: {school.name}")
        if not schools:
            print("   [NO SCHOOLS FOUND]")
        
        # Check Admin Users and their school_id
        print("\n2. ADMIN USERS:")
        admins = User.query.filter_by(role='admin').all()
        for admin in admins:
            superadmin_flag = " (SUPERADMIN)" if admin.is_superadmin else ""
            school_info = f"school_id={admin.school_id}" if admin.school_id else "school_id=NULL"
            print(f"   - {admin.username} ({admin.full_name}) {school_info}{superadmin_flag}")
        if not admins:
            print("   [NO ADMINS FOUND]")
        
        # Check Student Users and their school_id
        print("\n3. STUDENTS:")
        students = User.query.filter_by(role='student').all()
        total = len(students)
        print(f"   Total students: {total}")
        
        # Group by school_id
        by_school = {}
        for student in students:
            sid = student.school_id or "NULL"
            if sid not in by_school:
                by_school[sid] = []
            by_school[sid].append(student)
        
        print("   Students by school_id:")
        for sid, stds in sorted(by_school.items()):
            print(f"   - school_id={sid}: {len(stds)} students")
            if len(stds) <= 3:
                for s in stds:
                    print(f"     * {s.username} ({s.full_name}) - class: {s.student_class}")
        
        # Analyze the problem
        print("\n4. ANALYSIS:")
        admins_with_school = [a for a in admins if a.school_id]
        admins_without_school = [a for a in admins if not a.school_id and not a.is_superadmin]
        
        if admins_without_school and students:
            print(f"   ⚠️  PROBLEM FOUND:")
            print(f"   - {len(admins_without_school)} regular admin(s) have NO school_id assigned:")
            for a in admins_without_school:
                print(f"     * {a.username}")
            print(f"   - These admin(s) will see NO students when they log in!")
            print(f"   - Students exist but cannot be fetched due to school_id filtering")
            return "SCHOOL_ID_MISMATCH"
        
        if not students and admins:
            print(f"   ⚠️  NO STUDENTS FOUND:")
            print(f"   - {len(admins)} admin(s) exist but no students detected")
            return "NO_STUDENTS"
        
        if not admins:
            print(f"   ⚠️  NO ADMINS FOUND")
            return "NO_ADMINS"
        
        print("   ✓ Database looks OK")
        return "OK"

if __name__ == '__main__':
    result = diagnose()
    sys.exit(0 if result == "OK" else 1)
