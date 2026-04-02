#!/usr/bin/env python3
"""
Comprehensive diagnostic test for exam starting functionality.
Tests database schema, exam loading, session creation, and answer records.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from code1 import app, db, User, Exam, Question, ExamSession, Answer, Subject, School
from datetime import datetime
import json

def test_database_schema():
    """Test that all required tables and columns exist."""
    print("\n" + "="*60)
    print("TEST 1: DATABASE SCHEMA")
    print("="*60)
    
    with app.app_context():
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            # Check Answer table columns
            answer_cols = [c['name'] for c in inspector.get_columns('answer')]
            print(f"✓ Answer table columns: {answer_cols}")
            
            required_cols = ['id', 'exam_session_id', 'question_id', 'selected_answer', 'is_correct', 'text_response', 'marks_obtained']
            for col in required_cols:
                if col in answer_cols:
                    print(f"  ✓ {col}")
                else:
                    print(f"  ✗ MISSING: {col}")
                    return False
            
            # Check other tables
            tables = inspector.get_table_names()
            print(f"\n✓ Database tables: {tables}")
            return True
        except Exception as e:
            print(f"✗ Error checking schema: {e}")
            return False

def test_data_availability():
    """Test that we have schools, subjects, exams, and questions."""
    print("\n" + "="*60)
    print("TEST 2: DATA AVAILABILITY")
    print("="*60)
    
    with app.app_context():
        try:
            # Check schools
            schools = School.query.all()
            print(f"✓ Schools in database: {len(schools)}")
            if schools:
                for s in schools[:3]:
                    print(f"  - {s.id}: {s.name}")
            
            # Check subjects
            subjects = Subject.query.all()
            print(f"✓ Subjects in database: {len(subjects)}")
            if subjects:
                for s in subjects[:3]:
                    print(f"  - {s.id}: {s.name}")
            
            # Check exams
            exams = Exam.query.all()
            print(f"✓ Exams in database: {len(exams)}")
            if exams:
                for e in exams[:3]:
                    print(f"  - {e.id}: {e.code} ({e.title}), is_active={e.is_active}, subject_id={e.subject_id}")
            
            # Check questions
            questions = Question.query.all()
            print(f"✓ Questions in database: {len(questions)}")
            
            # Group by subject
            for subject in subjects[:3]:
                count = Question.query.filter_by(subject_id=subject.id).count()
                print(f"  - Subject {subject.id} ({subject.name}): {count} questions")
            
            # Check students
            students = User.query.filter_by(role='student').all()
            print(f"✓ Students in database: {len(students)}")
            if students:
                for s in students[:3]:
                    print(f"  - {s.id}: {s.username} ({s.full_name})")
            
            return len(exams) > 0 and len(questions) > 0 and len(students) > 0
        except Exception as e:
            print(f"✗ Error checking data: {e}")
            import traceback
            traceback.print_exc()
            return False

def test_exam_session_creation():
    """Test creating an exam session."""
    print("\n" + "="*60)
    print("TEST 3: EXAM SESSION CREATION")
    print("="*60)
    
    with app.app_context():
        try:
            # Get first student, exam, and questions
            student = User.query.filter_by(role='student').first()
            exam = Exam.query.filter_by(is_active=True).first()
            
            if not student:
                print("✗ No student found")
                return False
            if not exam:
                print("✗ No active exam found")
                return False
            
            print(f"Using student: {student.username} (id={student.id})")
            print(f"Using exam: {exam.code} (id={exam.id}, subject_id={exam.subject_id})")
            
            questions = Question.query.filter_by(subject_id=exam.subject_id).all()
            print(f"Questions for subject: {len(questions)}")
            
            if not questions:
                print("✗ No questions available for this exam's subject")
                return False
            
            # Try to create an exam session
            try:
                exam_session = ExamSession(
                    exam_id=exam.id,
                    student_id=student.id,
                    start_time=datetime.utcnow(),
                    status='in_progress'
                )
                db.session.add(exam_session)
                db.session.flush()  # Get the ID without committing
                session_id = exam_session.id
                print(f"✓ Created exam session: {session_id}")
                
                # Try to create answer records
                answers_created = 0
                for q in questions:
                    a = Answer(
                        exam_session_id=session_id,
                        question_id=q.id,
                        selected_answer=None,
                        is_correct=None,
                        text_response=None,
                        marks_obtained=None
                    )
                    db.session.add(a)
                    answers_created += 1
                
                db.session.commit()
                print(f"✓ Created {answers_created} answer records")
                
                # Verify answers were created
                answers = Answer.query.filter_by(exam_session_id=session_id).all()
                print(f"✓ Verified {len(answers)} answers in database")
                
                # Rollback for clean state
                db.session.rollback()
                
                return True
            except Exception as e:
                db.session.rollback()
                print(f"✗ Error during session creation: {e}")
                import traceback
                traceback.print_exc()
                return False
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

def test_question_fetching():
    """Test that questions are properly fetched and loadable."""
    print("\n" + "="*60)
    print("TEST 4: QUESTION FETCHING")
    print("="*60)
    
    with app.app_context():
        try:
            exam = Exam.query.filter_by(is_active=True).first()
            if not exam:
                print("✗ No active exam found")
                return False
            
            questions = Question.query.filter_by(subject_id=exam.subject_id).all()
            print(f"✓ Fetched {len(questions)} questions for subject {exam.subject_id}")
            
            if questions:
                q = questions[0]
                print(f"\nSample question:")
                print(f"  ID: {q.id}")
                print(f"  Subject ID: {q.subject_id}")
                print(f"  Question: {q.question_text[:50]}...")
                print(f"  Is Theory: {q.is_theory}")
                print(f"  Options: A={q.option_a}, B={q.option_b}, C={q.option_c}")
                print(f"  Correct Answer: {q.correct_answer}")
                print(f"  Marks: {q.marks}")
            
            return len(questions) > 0
        except Exception as e:
            print(f"✗ Error fetching questions: {e}")
            return False

def test_api_question_endpoint():
    """Test the API endpoint for getting questions."""
    print("\n" + "="*60)
    print("TEST 5: API QUESTION ENDPOINT")
    print("="*60)
    
    with app.app_context():
        try:
            # Create a test session
            student = User.query.filter_by(role='student').first()
            exam = Exam.query.filter_by(is_active=True).first()
            questions = Question.query.filter_by(subject_id=exam.subject_id).all()
            
            if not all([student, exam, questions]):
                print("✗ Missing test data")
                return False
            
            exam_session = ExamSession(
                exam_id=exam.id,
                student_id=student.id,
                start_time=datetime.utcnow(),
                status='in_progress'
            )
            db.session.add(exam_session)
            db.session.flush()
            
            for q in questions:
                a = Answer(
                    exam_session_id=exam_session.id,
                    question_id=q.id,
                    selected_answer=None,
                    is_correct=None,
                    text_response=None,
                    marks_obtained=None
                )
                db.session.add(a)
            
            db.session.commit()
            
            # Now test retrieving questions via the logic that would be in the API
            print(f"Session ID: {exam_session.id}")
            print(f"Total questions: {len(questions)}")
            
            # Simulate fetching question 0
            if questions:
                q = questions[0]
                answer = Answer.query.filter_by(
                    exam_session_id=exam_session.id,
                    question_id=q.id
                ).first()
                
                if answer:
                    print(f"✓ Found answer record for question 0")
                    print(f"  Question: {q.question_text[:50]}...")
                else:
                    print(f"✗ No answer record found for question 0")
            
            db.session.rollback()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Run all tests."""
    print("\n\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + " EXAM START DIAGNOSTIC TEST ".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    results = {}
    
    results['schema'] = test_database_schema()
    results['data'] = test_data_availability()
    results['session'] = test_exam_session_creation()
    results['questions'] = test_question_fetching()
    results['api'] = test_api_question_endpoint()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    print("\n" + ("="*60))
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
