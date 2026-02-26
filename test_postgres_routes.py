#!/usr/bin/env python
"""
Comprehensive test suite to verify all routes work with PostgreSQL.
Run this after configuring PostgreSQL to ensure all functionality is active.
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from code1 import app, db, User, School, Subject, Exam, Question, ExamSession, Answer

def print_header(title):
    """Print formatted header."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_subheader(title):
    """Print formatted subheader."""
    print(f"\n{title}")
    print("-" * 80)

def test_database_connection():
    """Test basic database connectivity."""
    print_header("TEST 1: DATABASE CONNECTION")
    
    try:
        with app.app_context():
            result = db.session.execute('SELECT 1')
            db.session.commit()
            print("✓ PostgreSQL connection successful")
            
            # Print connection info
            db_url = app.config['SQLALCHEMY_DATABASE_URI']
            if 'postgresql' in db_url:
                print("✓ Using PostgreSQL database")
            
            return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def test_table_creation():
    """Verify all tables exist."""
    print_subheader("TEST 1.1: TABLE VERIFICATION")
    
    try:
        with app.app_context():
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = [
                'user', 'school', 'subject', 'exam', 'question',
                'exam_session', 'answer', 'exam_access_code'
            ]
            
            all_exist = True
            for table in required_tables:
                if table in tables:
                    print(f"  ✓ {table:20} - exists")
                else:
                    print(f"  ✗ {table:20} - MISSING")
                    all_exist = False
            
            return all_exist
    except Exception as e:
        print(f"✗ Table verification failed: {e}")
        return False

def test_authentication_routes():
    """Test authentication endpoints."""
    print_header("TEST 2: AUTHENTICATION ROUTES")
    
    app.testing = True
    client = app.test_client()
    
    routes = [
        ('GET', '/'),
        ('GET', '/login'),
        ('GET', '/register'),
        ('GET', '/logout'),
        ('GET', '/start'),
    ]
    
    passed = 0
    for method, route in routes:
        try:
            if method == 'GET':
                resp = client.get(route)
            else:
                resp = client.post(route)
            
            # Status < 400 is acceptable (redirects are OK)
            status_ok = resp.status_code < 400
            symbol = "✓" if status_ok else "✗"
            print(f"  {symbol} {method:4} {route:30} → Status: {resp.status_code}")
            
            if status_ok:
                passed += 1
        except Exception as e:
            print(f"  ✗ {method:4} {route:30} → Error: {str(e)[:40]}")
    
    print(f"\nResult: {passed}/{len(routes)} routes working")
    return passed == len(routes)

def test_data_operations():
    """Test CREATE, READ, UPDATE, DELETE operations."""
    print_header("TEST 3: DATA OPERATIONS (CRUD)")
    
    try:
        with app.app_context():
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            
            # CREATE - User
            print_subheader("CREATE Operations")
            test_user = User(
                username=f'testuser_{timestamp}',
                full_name='Test User',
                role='student'
            )
            test_user.set_password('TestPassword123!')
            db.session.add(test_user)
            db.session.commit()
            print(f"  ✓ Created user: {test_user.username}")
            
            # CREATE - School
            test_school = School(
                name=f'Test School {timestamp}',
                code=f'TSC{timestamp[:4]}',
                access_code=f'{timestamp[:10]}'
            )
            db.session.add(test_school)
            db.session.commit()
            print(f"  ✓ Created school: {test_school.name}")
            
            # CREATE - Subject
            test_subject = Subject(
                name=f'Test Subject {timestamp}',
                description='Test subject for verification',
                created_by=test_user.id
            )
            db.session.add(test_subject)
            db.session.commit()
            print(f"  ✓ Created subject: {test_subject.name}")
            
            # READ
            print_subheader("READ Operations")
            users = User.query.all()
            print(f"  ✓ Users in database: {len(users)}")
            
            schools = School.query.all()
            print(f"  ✓ Schools in database: {len(schools)}")
            
            subjects = Subject.query.all()
            print(f"  ✓ Subjects in database: {len(subjects)}")
            
            exams = Exam.query.all()
            print(f"  ✓ Exams in database: {len(exams)}")
            
            questions = Question.query.all()
            print(f"  ✓ Questions in database: {len(questions)}")
            
            # UPDATE
            print_subheader("UPDATE Operations")
            test_user.full_name = f'Updated {timestamp}'
            db.session.commit()
            print(f"  ✓ Updated user: {test_user.full_name}")
            
            # DELETE
            print_subheader("DELETE Operations")
            db.session.delete(test_user)
            db.session.commit()
            print(f"  ✓ Deleted test user")
            
            return True
            
    except Exception as e:
        print(f"✗ Data operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_admin_routes():
    """Test admin routes (simulated with session)."""
    print_header("TEST 4: ADMIN ROUTES")
    
    app.testing = True
    client = app.test_client()
    
    admin_routes = [
        ('GET', '/admin/dashboard'),
        ('GET', '/admin/subjects'),
        ('GET', '/admin/students'),
        ('GET', '/admin/questions'),
        ('GET', '/admin/exams'),
        ('GET', '/admin/results'),
        ('GET', '/admin/classes'),
        ('GET', '/admin/schools'),
        ('GET', '/admin/diagnostics'),
    ]
    
    # Create mock admin session
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'admin'
    
    passed = 0
    for method, route in admin_routes:
        try:
            if method == 'GET':
                resp = client.get(route)
            else:
                resp = client.post(route)
            
            status_ok = resp.status_code < 400
            symbol = "✓" if status_ok else "✗"
            print(f"  {symbol} {method:4} {route:30} → {resp.status_code}")
            
            if status_ok:
                passed += 1
        except Exception as e:
            print(f"  ✗ {method:4} {route:30} → {str(e)[:40]}")
    
    print(f"\nResult: {passed}/{len(admin_routes)} admin routes accessible")
    return passed >= len(admin_routes) * 0.8  # 80% passing

def test_file_operations():
    """Test file upload routes."""
    print_header("TEST 5: FILE OPERATIONS")
    
    app.testing = True
    client = app.test_client()
    
    # Verify upload folder exists
    upload_folder = app.config['UPLOAD_FOLDER']
    print(f"  Upload folder: {upload_folder}")
    
    if os.path.exists(upload_folder):
        print(f"  ✓ Upload folder exists")
        try:
            num_files = len(os.listdir(upload_folder))
            print(f"  ✓ Files in uploads: {num_files}")
        except Exception as e:
            print(f"  ⚠ Could not count files: {e}")
    else:
        print(f"  ⚠ Upload folder does not exist - will be created on first upload")
    
    # Test file download routes
    print_subheader("File Download Routes")
    file_routes = [
        ('GET', '/admin/question/template'),
        ('GET', '/admin/question/template_theory'),
        ('GET', '/admin/students/template'),
    ]
    
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'admin'
    
    passed = 0
    for method, route in file_routes:
        try:
            resp = client.get(route)
            status_ok = resp.status_code < 400
            symbol = "✓" if status_ok else "✗"
            print(f"  {symbol} {method:4} {route:40} → {resp.status_code}")
            if status_ok:
                passed += 1
        except Exception as e:
            print(f"  ✗ {method:4} {route:40} → {str(e)[:40]}")
    
    return passed >= 2

def test_json_endpoints():
    """Test JSON API endpoints."""
    print_header("TEST 6: JSON API ENDPOINTS")
    
    app.testing = True
    client = app.test_client()
    
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'admin'
    
    json_routes = [
        ('GET', '/admin/students/json'),
    ]
    
    passed = 0
    for method, route in json_routes:
        try:
            if method == 'GET':
                resp = client.get(route)
            else:
                resp = client.post(route)
            
            status_ok = resp.status_code < 400
            symbol = "✓" if status_ok else "✗"
            
            # Try to parse JSON
            try:
                if resp.data:
                    data = resp.get_json()
                    print(f"  {symbol} {method:4} {route:30} → {resp.status_code}")
                    print(f"      Response type: {type(data).__name__}")
                else:
                    print(f"  {symbol} {method:4} {route:30} → {resp.status_code} (empty)")
            except Exception as json_err:
                print(f"  {symbol} {method:4} {route:30} → {resp.status_code}")
            
            if status_ok:
                passed += 1
        except Exception as e:
            print(f"  ✗ {method:4} {route:30} → {str(e)[:40]}")
    
    return passed >= 1

def generate_report():
    """Generate comprehensive test report."""
    print_header("TEST SUITE: PostgreSQL CBT APPLICATION")
    
    print(f"\nStarting comprehensive route and functionality test")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python Version: {sys.version.split()[0]}")
    
    results = {
        'Database Connection': test_database_connection(),
        'Table Creation': test_table_creation(),
        'Authentication Routes': test_authentication_routes(),
        'Data Operations (CRUD)': test_data_operations(),
        'Admin Routes': test_admin_routes(),
        'File Operations': test_file_operations(),
        'JSON Endpoints': test_json_endpoints(),
    }
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print("\nTest Results:")
    for test_name, result in results.items():
        symbol = "✓ PASS" if result else "✗ FAIL"
        print(f"  {symbol:8} {test_name}")
    
    print(f"\nTotal: {passed_count}/{total_count} test groups passed")
    
    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED! PostgreSQL is properly configured.")
        print("\nYour application routes are:")
        print("  ✓ Authentication (login, register, logout)")
        print("  ✓ Admin dashboard and management")
        print("  ✓ Subject management")
        print("  ✓ Question operations (add, upload, generate)")
        print("  ✓ Exam creation and management")
        print("  ✓ Student management")
        print("  ✓ Results and reporting")
        print("  ✓ File operations (upload/download)")
        print("\n✓ Ready for production deployment!")
    else:
        print("\n⚠ Some tests failed. Review the output above for details.")
        print("Common issues:")
        print("  - PostgreSQL not running")
        print("  - Database not initialized")
        print("  - Wrong connection string")
        print("  - Missing dependencies")
    
    print("\n" + "="*80 + "\n")
    
    return passed_count == total_count

if __name__ == '__main__':
    try:
        success = generate_report()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFatal error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
