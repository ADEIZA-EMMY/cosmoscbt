#!/usr/bin/env python
"""Quick diagnostic script to check exam/question data in the database."""
import sys
sys.path.insert(0, '.')
from code1 import app, db, Exam, Question, Subject

with app.app_context():
    print("\n=== DATABASE DIAGNOSTICS ===\n")
    
    # Check subjects
    subjects = Subject.query.all()
    print(f"Total Subjects: {len(subjects)}")
    for s in subjects[:3]:
        print(f"  - ID: {s.id} (type: {type(s.id).__name__}), Name: {s.name}")
    
    # Check questions
    questions = Question.query.all()
    print(f"\nTotal Questions: {len(questions)}")
    for q in questions[:3]:
        print(f"  - ID: {q.id}, Subject ID: {q.subject_id} (type: {type(q.subject_id).__name__}), Text: {q.question_text[:40]}")
    
    # Check exams
    exams = Exam.query.all()
    print(f"\nTotal Exams: {len(exams)}")
    for exam in exams:
        q_count = Question.query.filter_by(subject_id=exam.subject_id).count()
        print(f"  - Exam ID: {exam.id}, Subject ID: {exam.subject_id} (type: {type(exam.subject_id).__name__}), Questions: {q_count}")
        if q_count == 0:
            # Show all questions for this subject to debug
            all_q = Question.query.filter_by(subject_id=exam.subject_id).all()
            print(f"    -> Searched for subject_id={exam.subject_id}, found {len(all_q)}")
    
    print("\n=== END DIAGNOSTICS ===\n")
