#!/usr/bin/env python3
"""Diagnose why students are not showing - minimal version without pandas."""

import sqlite3

def diagnose_sqlite():
    try:
        conn = sqlite3.connect('cbt.db')
        cursor = conn.cursor()
        
        print("=" * 60)
        print("STUDENT VISIBILITY DIAGNOSIS (SQLITE)")
        print("=" * 60)
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()
        print(f"\n1. TABLES IN DATABASE: {len(tables)} found")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Count students
        cursor.execute("SELECT COUNT(*) FROM user WHERE role='student';")
        student_count = cursor.fetchone()[0]
        print(f"\n2. STUDENT COUNT: {student_count}")
        
        # Count admins
        cursor.execute("SELECT COUNT(*) FROM user WHERE role='admin';")
        admin_count = cursor.fetchone()[0]
        print(f"3. ADMIN COUNT: {admin_count}")
        
        # Show admin users and their school_id
        print(f"\n4. ADMIN DETAILS:")
        cursor.execute("SELECT id, username, full_name, school_id, is_superadmin FROM user WHERE role='admin';")
        for row in cursor.fetchall():
            admin_id, username, full_name, school_id, is_superadmin = row
            superadmin_flag = " (SUPERADMIN)" if is_superadmin else ""
            school_info = f"school_id={school_id}" if school_id else "school_id=NULL"
            print(f"   - {username} ({full_name}) {school_info}{superadmin_flag}")
        
        # Show schools
        print(f"\n5. SCHOOLS:")
        cursor.execute("SELECT id, name FROM school;")
        schools = cursor.fetchall()
        if schools:
            for school_id, name in schools:
                cursor.execute("SELECT COUNT(*) FROM user WHERE role='student' AND school_id=?", (school_id,))
                student_count_in_school = cursor.fetchone()[0]
                print(f"   - ID {school_id}: {name} ({student_count_in_school} students)")
        else:
            print("   [NO SCHOOLS]")
        
        # Show students grouped by school_id
        print(f"\n6. STUDENTS BY SCHOOL_ID:")
        cursor.execute("SELECT school_id, COUNT(*) FROM user WHERE role='student' GROUP BY school_id;")
        for school_id, count in cursor.fetchall():
            school_info = f"school_id={school_id}" if school_id else "school_id=NULL"
            print(f"   - {school_info}: {count} students")
        
        # Show first few students
        print(f"\n7. SAMPLE STUDENTS (first 5):")
        cursor.execute("SELECT username, full_name, student_class, school_id FROM user WHERE role='student' LIMIT 5;")
        for username, full_name, student_class, school_id in cursor.fetchall():
            school_info = f"school_id={school_id}" if school_id else "school_id=NULL"
            print(f"   - {username} ({full_name}) class={student_class} {school_info}")
        
        # Analysis
        print(f"\n8. ANALYSIS:")
        if admin_count > 0 and student_count > 0:
            cursor.execute("""
                SELECT COUNT(*) FROM user u1
                WHERE u1.role='admin' 
                AND u1.is_superadmin=0
                AND u1.school_id IS NULL
            """)
            admins_without_school = cursor.fetchone()[0]
            
            if admins_without_school > 0:
                print(f"   ⚠️  PROBLEM: {admins_without_school} non-superadmin with NO school_id")
                print(f"   These admins will see NO students due to school_id filtering!")
                cursor.execute("""
                    SELECT username FROM user
                    WHERE role='admin' AND is_superadmin=0 AND school_id IS NULL
                """)
                for row in cursor.fetchall():
                    print(f"      * {row[0]}")
            else:
                print("   ✓ All non-superadmin users have school_id assigned")
        
        conn.close()
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == '__main__':
    diagnose_sqlite()
