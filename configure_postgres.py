#!/usr/bin/env python
"""
PostgreSQL Configuration Helper for Flask CBT Application
This script helps set up and configure PostgreSQL for your application.
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

def print_header(text):
    """Print formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_step(step_num, text):
    """Print numbered step."""
    print(f"\n[Step {step_num}] {text}")
    print("-" * 70)

def create_env_file():
    """Create .env file with PostgreSQL configuration."""
    print_step(1, "Create .env Configuration File")
    
    env_path = Path('.env')
    
    if env_path.exists():
        response = input("  .env file already exists. Overwrite? (y/n): ").lower()
        if response != 'y':
            print("  Skipping .env creation")
            return False
    
    # Gather configuration
    print("\n  PostgreSQL Configuration:")
    db_host = input("  Database Host [localhost]: ").strip() or 'localhost'
    db_port = input("  Database Port [5432]: ").strip() or '5432'
    db_name = input("  Database Name [cbt_app]: ").strip() or 'cbt_app'
    db_user = input("  Database User [cbt_user]: ").strip() or 'cbt_user'
    db_pass = input("  Database Password: ").strip()
    
    if not db_pass:
        print("  ✗ Password required!")
        return False
    
    database_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    # Flask configuration
    print("\n  Flask Configuration:")
    flask_env = input("  Flask Environment [development]: ").strip() or 'development'
    secret_key = input("  Secret Key (leave empty to auto-generate): ").strip()
    
    if not secret_key:
        import secrets
        secret_key = secrets.token_hex(32)
        print(f"  Generated secret key: {secret_key[:20]}...")
    
    openai_key = input("  OpenAI API Key (optional, press Enter to skip): ").strip()
    
    # Create .env content
    env_content = f"""# PostgreSQL Connection
DATABASE_URL={database_url}

# Flask Configuration
FLASK_ENV={flask_env}
FLASK_DEBUG={"True" if flask_env == "development" else "False"}
SECRET_KEY={secret_key}

# OpenAI Integration (Optional)
{"OPENAI_API_KEY=" + openai_key if openai_key else "# OPENAI_API_KEY=your_key_here"}
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0.7

# AWS S3 (Optional - if using for file uploads)
# AWS_ACCESS_KEY_ID=your_access_key
# AWS_SECRET_ACCESS_KEY=your_secret_key
# AWS_S3_BUCKET=your_bucket_name

# Email Configuration (Optional)
# MAIL_SERVER=smtp.gmail.com
# MAIL_PORT=587
# MAIL_USERNAME=your_email@gmail.com
# MAIL_PASSWORD=your_app_password
# MAIL_USE_TLS=True

# Application Settings
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=uploads
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print(f"\n  ✓ .env file created successfully")
        return True
    except Exception as e:
        print(f"  ✗ Error creating .env: {e}")
        return False

def create_init_script():
    """Create database initialization script."""
    print_step(2, "Create Database Initialization Script")
    
    script_path = Path('init_postgres.py')
    
    init_script = '''#!/usr/bin/env python
"""Initialize PostgreSQL database with all tables and initial data."""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from code1 import app, db, init_db

def main():
    """Initialize database."""
    print("\\n" + "="*70)
    print("  PostgreSQL Database Initialization")
    print("="*70)
    
    print("\\n[1] Checking database connection...")
    try:
        with app.app_context():
            db.session.execute('SELECT 1')
            print("  ✓ Database connection successful")
    except Exception as e:
        print(f"  ✗ Database connection failed: {e}")
        print("\\n  Please check:")
        print("    - PostgreSQL is running")
        print("    - DATABASE_URL in .env is correct")
        print("    - Database and user exist")
        return False
    
    print("\\n[2] Creating tables...")
    try:
        with app.app_context():
            init_db()
            print("  ✓ Tables created/verified successfully")
    except Exception as e:
        print(f"  ✗ Table creation failed: {e}")
        return False
    
    print("\\n[3] Verifying data...")
    try:
        with app.app_context():
            from code1 import User, School, Subject, Exam
            
            users = User.query.count()
            schools = School.query.count()
            subjects = Subject.query.count()
            exams = Exam.query.count()
            
            print(f"  ✓ Users:     {users}")
            print(f"  ✓ Schools:   {schools}")
            print(f"  ✓ Subjects:  {subjects}")
            print(f"  ✓ Exams:     {exams}")
    except Exception as e:
        print(f"  ✗ Data verification failed: {e}")
        return False
    
    print("\\n" + "="*70)
    print("  ✓ DATABASE INITIALIZATION COMPLETE")
    print("="*70)
    print("\\nYour PostgreSQL database is ready!")
    print("Run: python code1.py")
    print("\\n")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
'''
    
    try:
        with open(script_path, 'w') as f:
            f.write(init_script)
        os.chmod(script_path, 0o755)
        print(f"  ✓ init_postgres.py created")
        return True
    except Exception as e:
        print(f"  ✗ Error creating script: {e}")
        return False

def verify_dependencies():
    """Verify required packages are installed."""
    print_step(3, "Verify Python Dependencies")
    
    required = {
        'Flask': 'flask',
        'Flask-SQLAlchemy': 'flask_sqlalchemy',
        'SQLAlchemy': 'sqlalchemy',
        'psycopg2': 'psycopg2',
        'python-dotenv': 'dotenv',
    }
    
    missing = []
    
    for name, import_name in required.items():
        try:
            __import__(import_name)
            print(f"  ✓ {name:20} installed")
        except ImportError:
            print(f"  ✗ {name:20} NOT installed")
            missing.append(name)
    
    if missing:
        print(f"\n  Missing packages: {', '.join(missing)}")
        print("\n  Install with:")
        print("    pip install -r requirements.txt")
        return False
    
    return True

def create_connection_test():
    """Create database connection test script."""
    print_step(4, "Create Connection Test Script")
    
    test_script = '''#!/usr/bin/env python
"""Test PostgreSQL connection without Flask overhead."""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    """Test raw PostgreSQL connection."""
    import psycopg2
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("✗ DATABASE_URL not found in .env")
        return False
    
    # Parse connection string
    # Format: postgresql://user:password@host:port/database
    try:
        # Remove 'postgresql://' prefix
        url = database_url.replace('postgresql://', '')
        user_pass, rest = url.split('@')
        user, password = user_pass.split(':')
        host_port, dbname = rest.split('/')
        host, port = host_port.split(':')
        
        print(f"\\nConnecting to PostgreSQL:")
        print(f"  Host:     {host}")
        print(f"  Port:     {port}")
        print(f"  Database: {dbname}")
        print(f"  User:     {user}")
        
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=dbname,
            user=user,
            password=password
        )
        
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()
        
        print(f"\\n✓ Connection successful!")
        print(f"✓ PostgreSQL version: {version[0].split(',')[0]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"\\n✗ Connection failed: {e}")
        return False

if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)
'''
    
    try:
        with open('test_db_connection.py', 'w') as f:
            f.write(test_script)
        os.chmod('test_db_connection.py', 0o755)
        print(f"  ✓ test_db_connection.py created")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def show_next_steps():
    """Display next steps."""
    print_step(5, "Next Steps")
    
    print("""
1. Initialize the database:
   python init_postgres.py

2. Test the application:
   python test_postgres_routes.py

3. Run the application:
   python code1.py

4. Open in browser:
   http://localhost:5000

5. Login with:
   Username: admin
   Password: admin123
   (or use superadmin dashboard at /6869)

For detailed documentation, see:
  POSTGRESQL_SETUP_GUIDE.md
""")

def main():
    """Main configuration workflow."""
    print_header("PostgreSQL Configuration Helper")
    print("This tool will help you set up PostgreSQL for your CBT application")
    
    steps = [
        (create_env_file, "Create .env configuration file"),
        (verify_dependencies, "Verify Python dependencies"),
        (create_init_script, "Create database initialization script"),
        (create_connection_test, "Create connection test utility"),
    ]
    
    results = {}
    
    for i, (func, description) in enumerate(steps, 1):
        print(f"\n[{i}/{len(steps)}] {description}...")
        try:
            results[description] = func()
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results[description] = False
    
    # Summary
    print_header("Configuration Summary")
    
    for desc, result in results.items():
        symbol = "✓" if result else "✗"
        print(f"  {symbol} {desc}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✓ Configuration completed successfully!")
        show_next_steps()
    else:
        print("\n⚠ Some steps failed. Please resolve the issues above.")
    
    return all_passed

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nConfiguration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
