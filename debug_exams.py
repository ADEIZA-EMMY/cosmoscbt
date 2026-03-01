#!/usr/bin/env python
"""Debug script to diagnose exam visibility issues"""
import os
import sys
from code1 import app, db, User, Exam, School

with app.app_context():
    # Get students
    students = User.query.filter_by(role='student').all()
    print(f"Total students: {len(students)}")
    if students:
        for i, s in enumerate(students[:3]):
            print(f"\nSTUDENT {i+1}: {s.username}")
            print(f"  - school_id: {s.school_id}")
            print(f"  - student_class: {getattr(s, 'student_class', 'N/A')}")
    
    # Get exams
    exams = Exam.query.all()
    print(f"\n\nTotal exams: {len(exams)}")
    if exams:
        for i, e in enumerate(exams[:5]):
            print(f"\nEXAM {i+1}: {e.title}")
            print(f"  - id: {e.id}")
            print(f"  - is_active: {e.is_active}")
            print(f"  - school_id: {e.school_id}")
            print(f"  - school_code: {getattr(e, 'school_code', 'N/A')}")
            print(f"  - allowed_classes: {getattr(e, 'allowed_classes', 'N/A')}")
            print(f"  - subject_class: {getattr(e, 'subject_class', 'N/A')}")
            print(f"  - created_by: {e.created_by}")
            creator = User.query.get(e.created_by)
            if creator:
                print(f"  - creator: {creator.username} (school_id={creator.school_id})")
    
    # Check if exams have NULL is_active
    null_active = db.session.execute(
        db.text("SELECT COUNT(*) FROM exam WHERE is_active IS NULL")
    ).scalar()
    print(f"\n\nExams with NULL is_active: {null_active}")
    
    # Check schools
    schools = School.query.all()
    print(f"Total schools: {len(schools)}")
    if schools:
        for s in schools[:3]:
            print(f"  - {s.name} (id={s.id}, code={s.code})")

print("\nDone.")
