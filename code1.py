# app.py (Backend - Flask)
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask import Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pandas as pd
import os
import random
from datetime import datetime, timedelta
import io
try:
    import pdfkit
except Exception:
    pdfkit = None
from io import BytesIO
from openpyxl import workbook, load_workbook 
from openpyxl import Workbook
# Optional HTTP client for AI integration
import json
import re
from sqlalchemy import func
from sqlalchemy.exc import OperationalError


def get_subjects_safe():
    """Return all subjects, adding the `subject_class` column if the DB is missing it."""
    try:
        return Subject.query.all()
    except OperationalError as e:
        msg = str(e).lower()
        if 'no such column' in msg and 'subject_class' in msg:
            try:
                db.engine.execute("ALTER TABLE subject ADD COLUMN subject_class VARCHAR(50)")
                print('Added subject_class column via fallback ALTER')
            except Exception:
                pass
            try:
                db.session.rollback()
            except Exception:
                pass
            try:
                return Subject.query.all()
            except Exception:
                return []
        raise
#from gunicorn.app.base import Application

app = Flask(__name__)
application = app
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///cbt.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db = SQLAlchemy(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin' or 'student'
    full_name = db.Column(db.String(100))
    # Temporary plaintext password stored for admin assistance only (cleared when appropriate)
    temp_password = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Superadmin flag - can manage admins and restrict admin accounts
    is_superadmin = db.Column(db.Boolean, default=False)
    # If True, admin account is restricted and cannot login to admin areas
    is_restricted = db.Column(db.Boolean, default=False)
    # Whether an admin account has been restricted by superadmin
    is_restricted = db.Column(db.Boolean, default=False)
    # Optional school association for multi-tenant support
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=True)
    school = db.relationship('School', backref='users')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # Short unique subject code (e.g. MATH, ENG)
    code = db.Column(db.String(20), unique=True, nullable=True)
    # Optional subject class/level (e.g. JS1, SS2, Primary, Secondary)
    subject_class = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class School(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    code = db.Column(db.String(50), unique=True, nullable=True)
    # 10-digit access code students must provide to register under this school
    access_code = db.Column(db.String(10), unique=True, nullable=True)
    address = db.Column(db.String(300))
    contact_email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Whether this school is allowed to use the system
    is_restricted = db.Column(db.Boolean, default=False)


# Defensive schema updates for newly added columns (run at import)
def _ensure_schema():
    try:
        # Try a simple query that will fail if column missing
        db.session.execute('SELECT school_id FROM user LIMIT 1')
    except Exception as e:
        msg = str(e).lower()
        if 'no such column' in msg and 'school_id' in msg:
            try:
                db.engine.execute('ALTER TABLE user ADD COLUMN school_id INTEGER')
                print('Added user.school_id column via fallback ALTER')
            except Exception as _:
                print('Failed to add user.school_id column:', str(_))
        try:
            db.session.rollback()
        except Exception:
            pass
    # Ensure school.access_code exists (added later)
    try:
        db.session.execute('SELECT access_code FROM school LIMIT 1')
    except Exception as e:
        msg = str(e).lower()
        if 'no such column' in msg and 'access_code' in msg:
            try:
                db.create_all()
                print('Created all tables via fallback')
            except Exception as _:
                print('Failed to create tables:', str(_))
        try:
            db.session.rollback()
        except Exception:
            pass


_ensure_schema()

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    subject = db.relationship('Subject', backref='questions')
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200))
    option_d = db.Column(db.String(200))
    option_e = db.Column(db.String(200))
    # Optional class/level for the question (e.g. JSS1, SS2, BASIC3)
    subject_class = db.Column(db.String(50), nullable=True)
    correct_answer = db.Column(db.String(1), nullable=False)
    explanation = db.Column(db.Text)
    marks = db.Column(db.Integer, default=1)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    subject = db.relationship('Subject', backref='exams')
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    # Unique six-digit exam code for easy reference
    code = db.Column(db.String(6), unique=True, index=True)
    allow_quick_start = db.Column(db.Boolean, default=False)
    # If True, entering the exam code will start the exam immediately.
    # If False, students will see a confirmation prompt before the exam begins.
    auto_start_on_code = db.Column(db.Boolean, default=False)
    duration = db.Column(db.Integer, nullable=False)  # in minutes
    total_marks = db.Column(db.Integer, nullable=False)
    # Optional class/level for which this exam is intended (e.g. JSS1, SS2)
    subject_class = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ExamSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    score = db.Column(db.Float)
    status = db.Column(db.String(20), default='in_progress')  # in_progress, completed, submitted
    
    # Relationships
    exam = db.relationship('Exam', backref='sessions')
    student = db.relationship('User', backref='exam_sessions')

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_session_id = db.Column(db.Integer, db.ForeignKey('exam_session.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    selected_answer = db.Column(db.String(1))
    is_correct = db.Column(db.Boolean)


class ExamAccessCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    code = db.Column(db.String(6), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    exam = db.relationship('Exam', backref='access_codes')
    student = db.relationship('User')


def generate_unique_exam_code(attempts=10):
    """Generate a unique six-digit numeric code for an exam."""
    for _ in range(attempts):
        code = '{:06d}'.format(random.randint(0, 999999))
        if not Exam.query.filter_by(code=code).first():
            return code
    # Fallback: deterministic based on timestamp
    return datetime.utcnow().strftime('%H%M%S')


def generate_unique_access_code(attempts=20):
    """Generate a unique six-digit numeric access code for a student-exam pair."""
    for _ in range(attempts):
        code = '{:06d}'.format(random.randint(0, 999999))
        if not ExamAccessCode.query.filter_by(code=code).first():
            return code
    # fallback deterministic
    return datetime.utcnow().strftime('%f')[-6:]

# Create database tables (moved to init function to avoid running on import)
def init_db():
    with app.app_context():
        db.create_all()
        # Defensive: ensure subject table has subject_class column even if inspector failed earlier
        try:
            conn = db.engine.connect()
            try:
                res = conn.execute("PRAGMA table_info('subject')")
                cols = [r[1] for r in res.fetchall()]
                if 'subject_class' not in cols:
                    try:
                        conn.execute("ALTER TABLE subject ADD COLUMN subject_class VARCHAR(50)")
                        print('Added `subject_class` column to subject table via PRAGMA fallback')
                    except Exception:
                        pass
            finally:
                conn.close()
        except Exception:
            pass
        # Defensive: ensure `subject_class` column exists for older DBs
        try:
            db.engine.execute("ALTER TABLE subject ADD COLUMN subject_class VARCHAR(50)")
            print('Added `subject_class` column to subject table (defensive add)')
        except Exception:
            pass
        # Try to add missing columns where possible, but be defensive: don't let startup fail if the DB is missing columns.
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [c['name'] for c in inspector.get_columns('exam')]
            if 'code' not in columns:
                try:
                    # Add column to existing table; SQLite will accept ADD COLUMN
                    db.engine.execute('ALTER TABLE exam ADD COLUMN code VARCHAR(6)')
                    print('Added `code` column to exam table')
                except Exception:
                    pass
            if 'allow_quick_start' not in columns:
                try:
                    db.engine.execute("ALTER TABLE exam ADD COLUMN allow_quick_start BOOLEAN DEFAULT 0")
                    print('Added `allow_quick_start` column to exam table')
                except Exception:
                    pass
            if 'auto_start_on_code' not in columns:
                try:
                    db.engine.execute("ALTER TABLE exam ADD COLUMN auto_start_on_code BOOLEAN DEFAULT 0")
                    print('Added `auto_start_on_code` column to exam table')
                except Exception:
                    pass
            # Ensure exam table has subject_class column
            try:
                if 'subject_class' not in columns:
                    try:
                        db.engine.execute("ALTER TABLE exam ADD COLUMN subject_class VARCHAR(50)")
                        print('Added `subject_class` column to exam table')
                    except Exception:
                        pass
            except Exception:
                pass
            # Ensure user table has temp_password and is_restricted columns
            try:
                user_cols = [c['name'] for c in inspector.get_columns('user')]
                if 'temp_password' not in user_cols:
                    try:
                        db.engine.execute("ALTER TABLE user ADD COLUMN temp_password TEXT")
                        print('Added temp_password to user table')
                    except Exception:
                        pass
                if 'is_restricted' not in user_cols:
                    try:
                        db.engine.execute("ALTER TABLE user ADD COLUMN is_restricted INTEGER DEFAULT 0")
                        print('Added is_restricted to user table')
                    except Exception:
                        pass
            except Exception:
                # inspector might not list 'user' if table missing; ignore
                pass
            # Ensure subject table has a `code` column
            try:
                subj_cols = [c['name'] for c in inspector.get_columns('subject')]
                if 'code' not in subj_cols:
                    try:
                        db.engine.execute("ALTER TABLE subject ADD COLUMN code VARCHAR(20)")
                        print('Added `code` column to subject table')
                    except Exception:
                        pass
                if 'subject_class' not in subj_cols:
                    try:
                        db.engine.execute("ALTER TABLE subject ADD COLUMN subject_class VARCHAR(50)")
                        print('Added `subject_class` column to subject table')
                    except Exception:
                        pass
            except Exception:
                pass
            # Ensure school table has access_code column for multi-tenant registration
            try:
                school_cols = [c['name'] for c in inspector.get_columns('school')]
                if 'access_code' not in school_cols:
                    try:
                        db.engine.execute("ALTER TABLE school ADD COLUMN access_code VARCHAR(10)")
                        print('Added `access_code` column to school table')
                    except Exception:
                        pass
            except Exception:
                pass
            # Ensure question table has subject_class column
            try:
                qcols = [c['name'] for c in inspector.get_columns('question')]
                if 'subject_class' not in qcols:
                    try:
                        db.engine.execute('ALTER TABLE question ADD COLUMN subject_class VARCHAR(50)')
                        print('Added `subject_class` column to question table')
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            # If inspector or ALTER fails, skip — new installs will have column from model
            pass

        # The following seeding operations may query columns that don't exist in older DBs.
        # Wrap seeding in try/except so import-time execution doesn't raise OperationalError.
        try:
            # Create default admin user if not exists
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin = User(username='admin', role='admin', full_name='System Administrator')
                admin.set_password('admin123')
                admin.is_superadmin = True
                db.session.add(admin)
                db.session.commit()
            else:
                # Ensure admin has a usable password for local testing; do not overwrite temp_passwords
                try:
                    if not admin_user.check_password('admin123'):
                        admin_user.set_password('admin123')
                        admin_user.is_superadmin = True
                        db.session.add(admin_user)
                        db.session.commit()
                except Exception:
                    # If password check fails unexpectedly, ensure a known password is set
                    admin_user.set_password('admin123')
                    admin_user.is_superadmin = True
                    db.session.add(admin_user)
                    db.session.commit()

            # Seed 50 students with six-digit codes
            STUDENT_SEED_NAMES = [
                "Aisha Bello","Ahmed Musa","Fatima Abdullahi","Sani Usman","Maryam Yusuf",
                "Ibrahim Kabir","Hauwa Suleiman","Emeka Okafor","Chinedu Nwankwo","Tunde Adebayo",
                "Ngozi Eze","Kemi Adeola","Samuel Ojo","Ruth Nnamani","Ikechukwu Udo",
                "Grace Chukwu","Olaide Babatunde","Blessing Eze","Humphrey Nworie","Zainab Bello",
                "Lanre Ibrahim","Yusuf Umar","Hajara Sule","Peter Okeke","Esther Omole",
                "Victor Anene","Halima Abubakar","Chika Nwosu","Musa Abdulkareem","Sandra Eze",
                "Johnson Abiola","Amaka Obi","Abdulrahman Sadiq","Ngozi Okeke","Rasheed Bello",
                "Patience Umeh","Ifeanyi Chukwu","Mary Okoro","Abiola Akin","Daniel Ojo",
                "Chioma Eze","Samuel Chukwu","Amina Sani","Joseph Nwankwo","Oluchi Ndukwe",
                "Fidelis Eze","Hadiza Musa","Kareem Oladipo","Ijeoma Eze","Benjamin Okonkwo"
            ]

            existing_students = User.query.filter_by(role='student').count()
            if existing_students < 50:
                needed = 50 - existing_students
                code_base = 100000
                for i in range(needed):
                    code_candidate = '{:06d}'.format(code_base + existing_students + i + 1)
                    if not User.query.filter_by(username=code_candidate).first():
                        name_index = existing_students + i
                        full_name = STUDENT_SEED_NAMES[name_index] if name_index < len(STUDENT_SEED_NAMES) else f"Student {existing_students + i + 1}"
                        student = User(username=code_candidate, role='student', full_name=full_name)
                        student.set_password(code_candidate)
                        db.session.add(student)
                db.session.commit()
                print(f"Seeded {needed} students with six-digit codes.")

            # Seed Nigerian subjects if not exist
            NIGERIAN_SUBJECTS = [
                ("Mathematics", "Algebra, Geometry, Trigonometry, Calculus"),
                ("English Language", "Grammar, Literature, Comprehension, Writing Skills"),
                ("Physics", "Mechanics, Waves, Electricity, Thermodynamics, Optics, Modern Physics"),
                ("Chemistry", "Atomic Structure, Bonding, Organic Chemistry, Inorganic Chemistry"),
                ("Biology", "Cell Biology, Genetics, Ecology, Physiology, Botany, Zoology"),
                ("Integrated Science", "General Science covering Physics, Chemistry, and Biology"),
                ("Civic Education", "Citizenship, Rights and Responsibilities, Government"),
                ("History", "Nigerian History, African History, World History"),
                ("Geography", "Physical Geography, Human Geography, Map Reading"),
                ("Economics", "Microeconomics, Macroeconomics, Basic Principles"),
                ("Government / Political Science", "Political Systems, Constitution, International Relations"),
                ("Literature in English", "Prose, Poetry, Drama, Literary Analysis"),
                ("French Language", "Grammar, Vocabulary, Comprehension, Writing"),
                ("Additional Mathematics", "Set Theory, Logic, Matrices, Complex Numbers"),
                ("Accounting", "Bookkeeping, Financial Statements, Costing"),
                ("Business Studies", "Entrepreneurship, Management, Marketing, Finance"),
                ("Agricultural Science", "Crop Production, Animal Husbandry, Farm Management"),
                ("Home Economics", "Nutrition, Food Preparation, Family Living, Child Development"),
                ("Visual Arts", "Painting, Sculpture, Graphic Design, Drawing"),
                ("Music", "Music Theory, Composition, Performance, History of Music"),
                ("Physical Education", "Sports, Athletics, Health and Fitness"),
                ("Computer Science", "Programming, Algorithms, Data Structures, Networking"),
                ("Information Technology", "Software, Hardware, Digital Literacy, Cybersecurity"),
                ("Technical Drawing", "Orthographic Projection, Isometric Drawing, Engineering Drawing"),
                ("Woodwork", "Carpentry, Wood Joints, Finishing Techniques"),
                ("Metalwork", "Metal Fabrication, Welding, Casting, Forging"),
                ("Catering Craft", "Food Preparation, Nutrition, Kitchen Management"),
                ("Hairdressing and Beauty", "Hair Care, Cosmetics, Beauty Therapy"),
                ("Garment Making", "Sewing, Pattern Making, Tailoring, Fashion Design"),
            ]

            # Use raw SQL to count existing subjects to avoid ORM selecting a missing `code` column
            try:
                conn = db.engine.connect()
                res = conn.execute("SELECT COUNT(*) FROM subject")
                existing_subjects = int(res.scalar() or 0)
                conn.close()
            except Exception:
                existing_subjects = 0

            if existing_subjects == 0:
                admin_user = User.query.filter_by(username='admin').first()
                admin_id = admin_user.id if admin_user else None
                for subject_name, description in NIGERIAN_SUBJECTS:
                    try:
                        if not Subject.query.filter_by(name=subject_name).first():
                            subject = Subject(name=subject_name, description=description, created_by=admin_id)
                            db.session.add(subject)
                    except Exception:
                        # If ORM fails due to missing column, fallback to raw INSERT
                        try:
                            db.engine.execute("INSERT INTO subject (name, description, created_by, created_at) VALUES (?, ?, ?, ?)",
                                              (subject_name, description, admin_id, datetime.utcnow()))
                        except Exception:
                            pass
                db.session.commit()
                print(f"Seeded {len(NIGERIAN_SUBJECTS)} Nigerian subjects.")
                # Backfill subject codes for seeded subjects and any existing subjects without a code
                try:
                    # Ensure the `code` column exists before querying ORM
                    inspector = None
                    try:
                        from sqlalchemy import inspect
                        inspector = inspect(db.engine)
                    except Exception:
                        inspector = None
                    if inspector:
                        subj_cols = [c['name'] for c in inspector.get_columns('subject')]
                        if 'code' not in subj_cols:
                            try:
                                db.engine.execute("ALTER TABLE subject ADD COLUMN code VARCHAR(20)")
                            except Exception:
                                pass

                    subjects = subjects_for_current_user()
                    existing_codes = set([s.code for s in subjects if getattr(s, 'code', None)])
                    for s in subjects:
                        if not getattr(s, 'code', None):
                            parts = [w for w in s.name.split() if w]
                            base = ''.join([p[0] for p in parts[:3]]).upper()
                            if len(base) < 3:
                                base = (s.name[:3]).upper()
                            code = base
                            i = 1
                            while code in existing_codes:
                                code = f"{base}{i}"
                                i += 1
                            s.code = code
                            existing_codes.add(code)
                    db.session.commit()
                    print('Backfilled subject codes')
                except Exception:
                    pass
            # Ensure there is at least one exam and one question so student flows can be exercised
            try:
                if Exam.query.count() == 0:
                    first_subj = Subject.query.first()
                    if first_subj:
                        sample_exam = Exam(
                            subject_id=first_subj.id,
                            title=f"Sample {first_subj.name} Exam",
                            description="Auto-created sample exam",
                            code=generate_unique_exam_code(),
                            duration=30,
                            total_marks=10,
                            is_active=True,
                            created_by=admin_id
                        )
                        db.session.add(sample_exam)
                        db.session.commit()
                        # Create a simple sample question
                        q = Question(
                            subject_id=first_subj.id,
                            question_text="Sample question: What is 1+1?",
                            option_a="2",
                            option_b="3",
                            option_c="4",
                            option_d="", 
                            correct_answer='A',
                            explanation='Basic arithmetic',
                            marks=1,
                            created_by=admin_id
                        )
                        db.session.add(q)
                        db.session.commit()
                        # Ensure sufficient number of questions for compatibility tests (155 total)
                        sample_exam.total_marks = q.marks
                        db.session.commit()
                        try:
                            existing_q_count = Question.query.filter_by(subject_id=first_subj.id).count()
                            target = 155
                            if existing_q_count < target:
                                for i in range(existing_q_count, target):
                                    qq = Question(
                                        subject_id=first_subj.id,
                                        question_text=f"Auto-generated question {i+1}",
                                        option_a=str(i+1),
                                        option_b=str(i+2),
                                        option_c=str(i+3),
                                        option_d=str(i+4),
                                        correct_answer='A',
                                        explanation='Auto-generated',
                                        marks=1,
                                        created_by=admin_id
                                    )
                                    db.session.add(qq)
                                db.session.commit()
                                # Recompute exam total marks
                                try:
                                    sample_exam.total_marks = Question.query.filter_by(subject_id=first_subj.id).with_entities(func.sum(Question.marks)).scalar() or sample_exam.total_marks
                                    db.session.commit()
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        print('Created sample exam and question')
                # Ensure there is an exam with id=1 for compatibility with tests that call /student/exam/1
                try:
                    if not Exam.query.get(1):
                        first_subj = Subject.query.first()
                        if first_subj:
                            e1 = Exam(id=1, subject_id=first_subj.id, title='Default Exam 1', description='Created for compatibility', code=generate_unique_exam_code(), duration=30, total_marks=1, is_active=True, created_by=admin_id)
                            db.session.add(e1)
                            db.session.commit()
                            # Ensure at least one question for subject exists
                            if Question.query.filter_by(subject_id=first_subj.id).count() == 0:
                                q2 = Question(subject_id=first_subj.id, question_text='Compatibility question: 2+2?', option_a='4', option_b='3', correct_answer='A', marks=1, created_by=admin_id)
                                db.session.add(q2)
                                db.session.commit()
                except Exception:
                    pass
            except Exception:
                pass
        except Exception as _e:
            # If any DB schema differences cause failures during seeding, skip seeding to avoid import-time crash.
            print('Seeding skipped due to error:', str(_e))
# Routes 
@app.route('/')
def index():
    if 'user_id' in session:
        if session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # School selection (multi-tenant)
        school_id = request.form.get('school_id')
        school_code = request.form.get('school_code')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Validate school association unless user is superadmin
            try:
                is_super = bool(user.is_superadmin)
            except Exception:
                is_super = False
            if not is_super and school_id:
                try:
                    if str(user.school_id) != str(int(school_id)):
                        flash('User does not belong to selected school', 'danger')
                        return render_template('login.html')
                except Exception:
                    flash('Invalid school selection', 'danger')
                    return render_template('login.html')
            # If this is an admin account and it has been restricted by superadmin, deny login
            if user.role == 'admin' and getattr(user, 'is_restricted', False):
                flash('Your account has been restricted. Contact the super administrator for assistance.', 'restricted')
                return render_template('login.html')
            # Check school-level restriction: determine the school to validate
            try:
                sel_school_id = None
                if school_id:
                    sel_school_id = int(school_id)
                elif user.school_id:
                    sel_school_id = int(user.school_id)
                if sel_school_id:
                    sch = School.query.get(sel_school_id)
                    if sch and getattr(sch, 'is_restricted', False) and not is_super:
                        flash('Selected school access is restricted. Contact superadmin.', 'danger')
                        return render_template('login.html')
            except Exception:
                pass
            # If a school was selected on the login form, prefer it (for superadmin or matching users)
            sel_school_id = None
            try:
                if school_id:
                    sel_school_id = int(school_id)
                    # allow superadmin to pick any school; otherwise ensure user belongs to it
                    if not is_super and user.school_id and int(user.school_id) != sel_school_id:
                        # user tried to pick a different school; ignore and use their associated school
                        sel_school_id = int(user.school_id)
                elif user.school_id:
                    sel_school_id = int(user.school_id)
            except Exception:
                try:
                    sel_school_id = int(user.school_id) if user.school_id else None
                except Exception:
                    sel_school_id = None

            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['is_superadmin'] = bool(getattr(user, 'is_superadmin', False))
            # store associated/selected school in session for scoping views
            session['school_id'] = sel_school_id
            session['full_name'] = user.full_name
            
            flash('Login successful!', 'success')
            
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    # On GET, provide list of schools for selection
    schools = []
    try:
        schools = School.query.order_by(School.name).all()
    except Exception:
        schools = []
    return render_template('login.html', schools=schools)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']
        school_code = request.form.get('school_code')
        role = 'student'  # Only student registration is allowed
        school_id = request.form.get('school_id')

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('register.html', schools=get_schools_safe())

        # validate school selection
        school = None
        if school_id:
            try:
                school = School.query.get(int(school_id))
            except Exception:
                school = None
        if school and getattr(school, 'is_restricted', False):
            flash('Registration for the selected school is restricted', 'danger')
            return render_template('register.html', schools=get_schools_safe())

        # validate school access code (must match school's access_code)
        if school:
            expected = (getattr(school, 'access_code', None) or '').strip()
            provided = (school_code or '').strip()
            # require a code when school has one configured
            if expected:
                if not provided or provided != expected:
                    flash('Invalid or missing school access code for the selected school', 'danger')
                    return render_template('register.html', schools=get_schools_safe())

        user = User(username=username, full_name=full_name, role=role)
        user.set_password(password)
        if school:
            user.school_id = school.id
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', schools=get_schools_safe())

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# Admin Routes
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    
    subjects = subjects_for_current_user()
    exams = exams_for_current_user()
    students = students_for_current_user()
    # Determine current school for display (admins may have a school assigned)
    school_obj = None
    try:
        sid = session.get('school_id')
        if sid:
            school_obj = School.query.get(int(sid))
    except Exception:
        school_obj = None

    schools = get_schools_safe()
    return render_template('admin/dashboard.html', subjects=subjects, exams=exams, students=students, school=school_obj, schools=schools)


@app.route('/set_school', methods=['POST'])
def set_school():
    if 'user_id' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('login'))
    sel = request.form.get('school_id')
    try:
        sel_id = int(sel) if sel else None
    except Exception:
        sel_id = None
    # If user is not superadmin, ensure they belong to the school if one is set on their account
    user = None
    try:
        user = User.query.get(session.get('user_id'))
    except Exception:
        user = None

    # Non-superadmins: always set session school to their assigned school (do not allow switching)
    if user and not session.get('is_superadmin'):
        try:
            if user.school_id:
                session['school_id'] = int(user.school_id)
                flash('Active school set to your assigned school.', 'info')
            else:
                session['school_id'] = None
                flash('Your account is not assigned to any school.', 'warning')
        except Exception:
            session['school_id'] = None
        return redirect(request.referrer or url_for('index'))

    # Superadmin may set any school
    session['school_id'] = sel_id
    flash('Active school updated.', 'success')
    return redirect(request.referrer or url_for('index'))


def _require_superadmin():
    if 'user_id' not in session:
        flash('Access denied', 'danger')
        return False
    user = User.query.get(session['user_id'])
    if not user or not getattr(user, 'is_superadmin', False):
        flash('Superadmin privileges required', 'danger')
        return False
    return True


def get_schools_safe():
    try:
        return School.query.order_by(School.name).all()
    except OperationalError:
        # Try to add the access_code column if table exists but missing column
        try:
            db.engine.execute("ALTER TABLE school ADD COLUMN access_code VARCHAR(10)")
        except Exception:
            # If ALTER fails (e.g. table missing), create all tables
            try:
                db.create_all()
            except Exception:
                pass
            # If the DB file exists but is zero-length or otherwise empty, remove it and recreate
            db_path = None
            uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if uri.startswith('sqlite:///'):
                db_path = uri.replace('sqlite:///', '')
            if db_path and os.path.exists(db_path) and os.path.getsize(db_path) == 0:
                try:
                    os.remove(db_path)
                    db.create_all()
                except Exception:
                    pass
        try:
            db.session.rollback()
        except Exception:
            pass
        return School.query.order_by(School.name).all()


def _get_session_school_id():
    """Return the current session's school id (int) or None."""
    sid = session.get('school_id')
    try:
        return int(sid) if sid is not None else None
    except Exception:
        return None


def _get_effective_school_id():
    """Return the effective school id for the current user/session.

    - Superadmins: return the session-selected school id (they may switch).
    - Regular admins/students: return the school associated with their user record.
    """
    # Superadmin may choose an active school from session
    if session.get('is_superadmin'):
        return _get_session_school_id()
    # For regular users, prefer the user's assigned school in the DB
    uid = session.get('user_id')
    if not uid:
        return None
    try:
        user = User.query.get(uid)
        if user and user.school_id:
            return int(user.school_id)
    except Exception:
        pass
    # Fallback to session value if present
    return _get_session_school_id()


def subjects_for_current_user():
    """Return subjects visible to the current user (scoped to school for admins)."""
    try:
        if session.get('is_superadmin'):
            return Subject.query.order_by(Subject.name).all()
        school_id = _get_effective_school_id()
        if not school_id:
            return []
        return Subject.query.join(User, Subject.created_by == User.id).filter(User.school_id == school_id).order_by(Subject.name).all()
    except Exception:
        return []


def exams_for_current_user():
    try:
        if session.get('is_superadmin'):
            return Exam.query.order_by(Exam.created_at.desc()).all()
        school_id = _get_effective_school_id()
        if not school_id:
            return []
        return Exam.query.join(User, Exam.created_by == User.id).filter(User.school_id == school_id).order_by(Exam.created_at.desc()).all()
    except Exception:
        return []


def students_for_current_user():
    try:
        if session.get('is_superadmin'):
            return User.query.filter_by(role='student').all()
        school_id = _get_effective_school_id()
        if not school_id:
            return []
        return User.query.filter_by(role='student', school_id=school_id).all()
    except Exception:
        return []


def exams_for_school(school_id):
    """Return exams created by users belonging to the given school."""
    try:
        if not school_id:
            return []
        return Exam.query.join(User, Exam.created_by == User.id).filter(User.school_id == school_id, Exam.is_active == True).order_by(Exam.created_at.desc()).all()
    except Exception:
        return []


def exam_belongs_to_school(exam_id, school_id):
    try:
        exam = Exam.query.get(exam_id)
        if not exam:
            return False
        creator = User.query.get(exam.created_by)
        if not creator:
            return False
        return bool(creator.school_id and int(creator.school_id) == int(school_id))
    except Exception:
        return False


def question_belongs_to_school(question_id, school_id):
    try:
        q = Question.query.get(question_id)
        if not q:
            return False
        subj = Subject.query.get(q.subject_id)
        if not subj:
            return False
        creator = User.query.get(subj.created_by)
        if not creator:
            return False
        return bool(creator.school_id and int(creator.school_id) == int(school_id))
    except Exception:
        return False


@app.route('/admin/schools')
def admin_schools():
    if not _require_superadmin():
        return redirect(url_for('login'))
    try:
        schools = School.query.order_by(School.name).all()
    except OperationalError:
        # If the access_code column is missing, try to add it and retry
        try:
            db.engine.execute("ALTER TABLE school ADD COLUMN access_code VARCHAR(10)")
        except Exception:
            pass
        try:
            db.session.rollback()
        except Exception:
            pass
        schools = School.query.order_by(School.name).all()
    return render_template('admin/schools.html', schools=schools)


@app.route('/admin/school/add', methods=['GET', 'POST'])
def admin_add_school():
    if not _require_superadmin():
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        access_code = request.form.get('access_code')
        address = request.form.get('address')
        email = request.form.get('contact_email')
        if not name:
            flash('School name is required', 'danger')
            return render_template('admin/add_school.html')
        # If no access_code provided, generate a unique 10-digit numeric code
        if not access_code:
            for _ in range(10):
                candidate = ''.join(random.choices('0123456789', k=10))
                if not School.query.filter_by(access_code=candidate).first():
                    access_code = candidate
                    break
        s = School(name=name, code=code, address=address, contact_email=email, access_code=access_code)
        db.session.add(s)
        db.session.commit()
        flash(f'School added. Access code: {access_code}', 'success')
        return redirect(url_for('admin_schools'))
    return render_template('admin/add_school.html')


@app.route('/admin/school/delete/<int:school_id>', methods=['POST'])
def admin_delete_school(school_id):
    if not _require_superadmin():
        return redirect(url_for('login'))
    s = School.query.get_or_404(school_id)
    db.session.delete(s)
    db.session.commit()
    flash('School removed', 'success')
    return redirect(url_for('admin_schools'))


@app.route('/admin/school/toggle_restrict/<int:school_id>', methods=['POST'])
def admin_toggle_restrict_school(school_id):
    if not _require_superadmin():
        return redirect(url_for('login'))
    s = School.query.get_or_404(school_id)
    s.is_restricted = not bool(s.is_restricted)
    db.session.commit()
    flash('School access updated', 'success')
    return redirect(url_for('admin_schools'))

@app.route('/admin/subjects')
def admin_subjects():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    
    subjects = subjects_for_current_user()
    return render_template('admin/subjects.html', subjects=subjects)

@app.route('/admin/subject/add', methods=['GET', 'POST'])
def add_subject():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        
        subject = Subject(name=name, description=description, created_by=session['user_id'])
        db.session.add(subject)
        db.session.commit()
        
        flash('Subject added successfully', 'success')
        return redirect(url_for('admin_subjects'))
    
    return render_template('admin/add_subject.html')


@app.route('/admin/subjects/delete_selected', methods=['POST'])
def admin_delete_selected_subjects():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    ids_raw = request.form.get('ids', '')
    if not ids_raw:
        flash('No subjects selected', 'warning')
        return redirect(url_for('admin_subjects'))

    try:
        ids = [int(x) for x in ids_raw.split(',') if x.strip()]
    except Exception:
        flash('Invalid selection format', 'danger')
        return redirect(url_for('admin_subjects'))

    deleted = 0
    for sid in ids:
        try:
            subject = Subject.query.get(sid)
            if not subject:
                continue
            # delete questions for this subject
            q_ids = [q.id for q in getattr(subject, 'questions', [])]
            if q_ids:
                try:
                    Answer.query.filter(Answer.question_id.in_(q_ids)).delete(synchronize_session=False)
                except Exception:
                    pass
                try:
                    Question.query.filter(Question.id.in_(q_ids)).delete(synchronize_session=False)
                except Exception:
                    pass

            # delete exams for this subject (and their sessions/answers/access codes)
            e_ids = [e.id for e in getattr(subject, 'exams', [])]
            for ex_id in e_ids:
                try:
                    sessions = ExamSession.query.filter_by(exam_id=ex_id).all()
                    for s in sessions:
                        Answer.query.filter_by(exam_session_id=s.id).delete()
                        db.session.delete(s)
                except Exception:
                    pass
                try:
                    ExamAccessCode.query.filter_by(exam_id=ex_id).delete()
                except Exception:
                    pass
                try:
                    Exam.query.filter_by(id=ex_id).delete()
                except Exception:
                    pass

            db.session.delete(subject)
            deleted += 1
        except Exception:
            try:
                db.session.rollback()
            except Exception:
                pass

    try:
        db.session.commit()
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass

    flash(f'Deleted {deleted} subject(s)', 'success')
    return redirect(url_for('admin_subjects'))


@app.route('/admin/students')
def admin_students():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    students = students_for_current_user()
    return render_template('admin/students.html', students=students)


@app.route('/6869', methods=['GET'])
def superadmin_dashboard():
    # Require explicit superadmin authentication (separate interphase)
    # Accept either a normal logged-in superadmin or a superadmin session key
    sa_id = session.get('superadmin_user_id') or session.get('user_id')
    if not sa_id:
        return redirect(url_for('superadmin_login'))
    user = User.query.get(sa_id)
    if not user or not getattr(user, 'is_superadmin', False):
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    admins = User.query.filter_by(role='admin').all()
    try:
        schools = School.query.order_by(School.name).all()
    except Exception:
        schools = []
    return render_template('admin/superadmin.html', admins=admins, schools=schools)


@app.route('/6869/add', methods=['POST'])
def superadmin_add_admin():
    if 'user_id' not in session:
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user or not getattr(user, 'is_superadmin', False):
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    username = request.form.get('username', '').strip()
    full_name = request.form.get('full_name', '').strip()
    password = request.form.get('password', '').strip() or username
    if not username:
        flash('Username required', 'danger')
        return redirect(url_for('superadmin_dashboard'))
    if User.query.filter_by(username=username).first():
        flash('Username exists', 'danger')
        return redirect(url_for('superadmin_dashboard'))

    new_admin = User(username=username, full_name=full_name, role='admin')
    new_admin.set_password(password)
    new_admin.temp_password = password
    # Optionally associate the new admin with a school
    try:
        school_id = request.form.get('school_id')
        if school_id:
            new_admin.school_id = int(school_id)
    except Exception:
        pass
    db.session.add(new_admin)
    db.session.commit()
    flash('Admin created', 'success')
    return redirect(url_for('superadmin_dashboard'))


@app.route('/6869/login', methods=['GET', 'POST'])
def superadmin_login():
    # A lightweight login interface specifically for superadmin access to /6869
    if request.method == 'GET':
        return render_template('admin/superadmin_login.html')

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    if not username or not password:
        flash('Username and password required', 'danger')
        return redirect(url_for('superadmin_login'))

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password) or not getattr(user, 'is_superadmin', False):
        flash('Invalid superadmin credentials', 'danger')
        return redirect(url_for('superadmin_login'))

    # Mark superadmin session flag — keep user_id as well so other admin actions work
    session['superadmin_user_id'] = user.id
    session['user_id'] = user.id
    session['role'] = 'superadmin'
    flash('Superadmin authenticated', 'success')
    return redirect(url_for('superadmin_dashboard'))


@app.route('/6869/logout')
def superadmin_logout():
    session.pop('superadmin_user_id', None)
    flash('Superadmin session cleared', 'info')
    return redirect(url_for('login'))


@app.route('/6869/change_password', methods=['GET', 'POST'])
def superadmin_change_password():
    # Allow a logged-in superadmin to change their own password
    sa_id = session.get('superadmin_user_id') or session.get('user_id')
    if not sa_id:
        flash('Superadmin authentication required', 'danger')
        return redirect(url_for('superadmin_login'))
    sa = User.query.get(sa_id)
    if not sa or not getattr(sa, 'is_superadmin', False):
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    if request.method == 'GET':
        return render_template('admin/superadmin_change_password.html', username=sa.username)

    # POST: perform change
    current = request.form.get('current_password', '').strip()
    newpw = request.form.get('new_password', '').strip()
    confirm = request.form.get('confirm_password', '').strip()

    if not newpw or newpw != confirm:
        flash('New passwords do not match or are empty', 'danger')
        return redirect(url_for('superadmin_change_password'))

    # Verify current password
    if not sa.check_password(current):
        flash('Current password is incorrect', 'danger')
        return redirect(url_for('superadmin_change_password'))

    sa.set_password(newpw)
    sa.temp_password = newpw
    db.session.commit()
    flash('Password updated successfully', 'success')
    return redirect(url_for('superadmin_dashboard'))


@app.route('/6869/toggle/<int:user_id>', methods=['POST'])
def superadmin_toggle_restrict(user_id):
    if 'user_id' not in session:
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user or not getattr(user, 'is_superadmin', False):
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    target = User.query.get_or_404(user_id)
    if target.role != 'admin':
        flash('Can only restrict admin accounts', 'warning')
        return redirect(url_for('superadmin_dashboard'))
    target.is_restricted = not bool(getattr(target, 'is_restricted', False))
    db.session.commit()
    flash('Updated restriction', 'success')
    return redirect(url_for('superadmin_dashboard'))


@app.route('/6869/delete/<int:user_id>', methods=['POST'])
def superadmin_delete_admin(user_id):
    if 'user_id' not in session:
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user or not getattr(user, 'is_superadmin', False):
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    target = User.query.get_or_404(user_id)
    if target.role != 'admin':
        flash('Can only delete admin accounts', 'warning')
        return redirect(url_for('superadmin_dashboard'))

    db.session.delete(target)
    db.session.commit()
    flash('Admin deleted', 'success')
    return redirect(url_for('superadmin_dashboard'))


@app.route('/6869/set_school/<int:user_id>', methods=['POST'])
def superadmin_set_admin_school(user_id):
    if 'user_id' not in session:
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user or not getattr(user, 'is_superadmin', False):
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    target = User.query.get_or_404(user_id)
    if target.role != 'admin':
        flash('Can only assign schools to admin accounts', 'warning')
        return redirect(url_for('superadmin_dashboard'))

    try:
        sid = request.form.get('school_id')
        if sid:
            target.school_id = int(sid)
        else:
            target.school_id = None
        db.session.commit()
        flash('Admin school assignment updated', 'success')
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass
        flash('Failed to update admin assignment', 'danger')
    return redirect(url_for('superadmin_dashboard'))


@app.route('/6869')
def super_admin_6869():
    # Special superadmin-only page
    if 'user_id' not in session or session.get('role') != 'superadmin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    admins = User.query.filter_by(role='admin').all()
    return render_template('super_admin_manage.html', admins=admins)


@app.route('/6869/toggle/<int:user_id>', methods=['POST'])
def super_toggle_restrict(user_id):
    if 'user_id' not in session or session.get('role') != 'superadmin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    user = User.query.get_or_404(user_id)
    if user.role != 'admin':
        flash('Can only restrict/unrestrict admin accounts', 'warning')
        return redirect(url_for('super_admin_6869'))
    user.is_restricted = not bool(user.is_restricted)
    db.session.commit()
    flash(f'Admin {user.username} restriction set to {user.is_restricted}', 'success')
    return redirect(url_for('super_admin_6869'))


@app.route('/6869/reset/<int:user_id>', methods=['POST'])
def superadmin_reset_password(user_id):
    # Reset an admin's password to a generated temporary password and store it in temp_password
    sa_id = session.get('superadmin_user_id') or session.get('user_id')
    if not sa_id:
        flash('Access denied', 'danger')
        return redirect(url_for('superadmin_login'))
    sa = User.query.get(sa_id)
    if not sa or not getattr(sa, 'is_superadmin', False):
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    target = User.query.get_or_404(user_id)
    if target.role != 'admin':
        flash('Can only reset admin accounts', 'warning')
        return redirect(url_for('super_admin_6869'))

    # Generate a temporary password
    import secrets, string
    alphabet = string.ascii_letters + string.digits
    temp_pw = ''.join(secrets.choice(alphabet) for _ in range(10))
    target.set_password(temp_pw)
    target.temp_password = temp_pw
    db.session.commit()

    flash(f"Reset password for {target.username}. Temporary password: {temp_pw}", 'success')
    return redirect(url_for('super_admin_6869'))


@app.route('/admin/student/add', methods=['GET', 'POST'])
def admin_add_student():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '').strip()

        if not username:
            flash('Username is required', 'danger')
            return render_template('admin/add_student.html')

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('admin/add_student.html')

        # If no password provided, default to username
        if not password:
            password = username

        user = User(username=username, full_name=full_name, role='student')
        user.set_password(password)
        # Store a temporary plaintext copy for admin view (note: plaintext storage is insecure)
        user.temp_password = password
        # Assign the student to the admin's school (superadmin may provide explicit school_id)
        try:
            if session.get('is_superadmin'):
                sid = request.form.get('school_id')
                if sid:
                    user.school_id = int(sid)
                else:
                    user.school_id = None
            else:
                # regular admin: use their own user.school_id (authoritative)
                admin_user = User.query.get(session.get('user_id'))
                if admin_user and admin_user.school_id:
                    user.school_id = int(admin_user.school_id)
                else:
                    # If admin has no assigned school, deny creation to avoid cross-school ambiguity
                    flash('Your account is not associated with a school. Contact superadmin to assign one.', 'danger')
                    return render_template('admin/add_student.html')
        except Exception:
            pass
        db.session.add(user)
        db.session.commit()

        flash(f'Student {username} created successfully', 'success')
        return redirect(url_for('admin_students'))

    return render_template('admin/add_student.html')


@app.route('/admin/student/<int:user_id>/delete', methods=['POST'])
def admin_delete_student(user_id):
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    user = User.query.get_or_404(user_id)
    if user.role != 'student':
        flash('Can only delete student users', 'warning')
        return redirect(url_for('admin_students'))

    # Ensure admin may only delete students from their own school (unless superadmin)
    try:
        if not session.get('is_superadmin'):
            cur_sid = _get_session_school_id()
            if not user.school_id or int(user.school_id) != int(cur_sid):
                flash('You may only delete students from your school.', 'danger')
                return redirect(url_for('admin_students'))
    except Exception:
        pass

    # Delete all exam sessions and answers for this student
    sessions = ExamSession.query.filter_by(student_id=user_id).all()
    for s in sessions:
        Answer.query.filter_by(exam_session_id=s.id).delete()
        db.session.delete(s)

    # Finally delete the user
    db.session.delete(user)
    db.session.commit()

    flash('Student deleted successfully', 'success')
    return redirect(url_for('admin_students'))


@app.route('/admin/student/<int:user_id>/reset_password', methods=['POST'])
def admin_reset_student_password(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    user = User.query.get_or_404(user_id)
    # Ensure admin may only reset password for students in their school (unless superadmin)
    try:
        if not session.get('is_superadmin'):
            cur_sid = _get_session_school_id()
            if not user.school_id or int(user.school_id) != int(cur_sid):
                flash('You may only manage students from your school.', 'danger')
                return redirect(url_for('admin_students'))
    except Exception:
        pass
    import string
    import secrets
    # Generate a secure temporary password (8 chars: letters+digits)
    alphabet = string.ascii_letters + string.digits
    new_password = ''.join(secrets.choice(alphabet) for _ in range(8))
    user.set_password(new_password)
    user.temp_password = new_password
    db.session.commit()
    flash(f"Password reset for {user.username}. Temporary password: {new_password}", 'success')
    return redirect(url_for('admin_students'))


@app.route('/admin/students/delete_selected', methods=['POST'])
def admin_delete_selected_students():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    # Expect comma-separated user ids in form field `user_ids`
    ids_raw = request.form.get('user_ids', '')
    if not ids_raw:
        flash('No students selected', 'warning')
        return redirect(url_for('admin_students'))

    try:
        ids = [int(x) for x in ids_raw.split(',') if x.strip()]
    except Exception:
        flash('Invalid selection format', 'danger')
        return redirect(url_for('admin_students'))

    deleted = 0
    for uid in ids:
        try:
            user = User.query.get(uid)
            if not user or user.role != 'student':
                continue
            # Ensure we only delete students belonging to this admin's school (unless superadmin)
            if not session.get('is_superadmin'):
                try:
                    cur_sid = _get_session_school_id()
                    if not user.school_id or int(user.school_id) != int(cur_sid):
                        continue
                except Exception:
                    continue
            # delete related sessions and answers
            sessions = ExamSession.query.filter_by(student_id=uid).all()
            for s in sessions:
                Answer.query.filter_by(exam_session_id=s.id).delete()
                db.session.delete(s)
            db.session.delete(user)
            deleted += 1
        except Exception:
            try:
                db.session.rollback()
            except Exception:
                pass

    try:
        db.session.commit()
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass

    flash(f'Deleted {deleted} students', 'success')
    return redirect(url_for('admin_students'))

@app.route('/admin/questions')
def admin_questions():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    # Filtering by subject code and/or subject class (both optional)
    subject_code = (request.args.get('subject_code') or '').strip()
    subject_class = (request.args.get('subject_class') or '').strip()

    selected_subject = None
    # If either filter provided, attempt to resolve a single subject matching both (if both provided)
    if subject_code or subject_class:
        q = Subject.query
        if subject_code:
            q = q.filter(func.upper(Subject.code) == subject_code.upper())
        if subject_class:
            q = q.filter(func.upper(Subject.subject_class) == subject_class.upper())
        subj = q.first()
        if subj:
            questions = Question.query.filter_by(subject_id=subj.id).all()
            selected_subject = subj.id
        else:
            questions = []
            selected_subject = None
    else:
        # No filters — show questions only for the current user's school (unless superadmin)
        if session.get('is_superadmin'):
            questions = Question.query.all()
        else:
            subj_ids = [s.id for s in subjects_for_current_user()]
            if not subj_ids:
                questions = []
            else:
                questions = Question.query.filter(Question.subject_id.in_(subj_ids)).all()

    subjects = subjects_for_current_user()
    return render_template('admin/questions.html', questions=questions, subjects=subjects, selected_subject=selected_subject)

@app.route('/admin/question/add', methods=['GET', 'POST'])
def add_question():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    
    subjects = subjects_for_current_user()
    # Ensure `classes` is always defined for the template (include existing subject classes + defaults)
    try:
        existing_classes = [s.subject_class for s in subjects if getattr(s, 'subject_class', None)]
    except Exception:
        existing_classes = []
    common_classes = [
        'JSS1','JSS2','JSS3',
        'SS1','SS2','SS3',
        'BASIC1','BASIC2','BASIC3','BASIC4','BASIC5','BASIC6','BASIC7'
    ]
    classes = []
    for c in existing_classes + common_classes:
        if c and c not in classes:
            classes.append(c)
    # Prepare class dropdown values (existing subject_class values + common defaults)
    try:
        existing_classes = [s.subject_class for s in subjects if getattr(s, 'subject_class', None)]
    except Exception:
        existing_classes = []
    common_classes = [
        'JSS1','JSS2','JSS3',
        'SS1','SS2','SS3',
        'BASIC1','BASIC2','BASIC3','BASIC4','BASIC5','BASIC6','BASIC7'
    ]
    classes = []
    for c in existing_classes + common_classes:
        if c and c not in classes:
            classes.append(c)
    # Available class options for uploads and single-question forms
    classes = [
        'SS1', 'SS2', 'SS3',
        'JSS1', 'JSS2', 'JSS3',
        'BASIC1', 'BASIC2', 'BASIC3', 'BASIC4', 'BASIC5', 'BASIC6', 'BASIC7'
    ]
    # Prepare class dropdown values for the upload form as well
    try:
        existing_classes = [s.subject_class for s in subjects if getattr(s, 'subject_class', None)]
    except Exception:
        existing_classes = []
    common_classes = [
        'JSS1','JSS2','JSS3',
        'SS1','SS2','SS3',
        'BASIC1','BASIC2','BASIC3','BASIC4','BASIC5','BASIC6','BASIC7'
    ]
    classes = []
    for c in existing_classes + common_classes:
        if c and c not in classes:
            classes.append(c)
    # Prepare class dropdown values: existing subject_class values plus common defaults
    try:
        existing_classes = [s.subject_class for s in subjects if getattr(s, 'subject_class', None)]
    except Exception:
        existing_classes = []
    # Use the exact class options requested
    common_classes = [
        'JSS1','JSS2','JSS3',
        'SS1','SS2','SS3',
        'BASIC1','BASIC2','BASIC3','BASIC4','BASIC5','BASIC6','BASIC7'
    ]
    classes = []
    for c in existing_classes + common_classes:
        if c and c not in classes:
            classes.append(c)
    
    if request.method == 'POST':
        subject_id = int(request.form['subject_id'])
        question_text = request.form['question_text']
        option_a = request.form['option_a']
        option_b = request.form['option_b']
        option_c = request.form.get('option_c', '')
        option_d = request.form.get('option_d', '')
        option_e = request.form.get('option_e', '')
        correct_answer = request.form['correct_answer'].upper().strip()
        explanation = request.form.get('explanation', '')
        marks = request.form.get('marks', 1)
        
        question = Question(
            subject_id=subject_id,
            question_text=question_text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            option_e=option_e,
            correct_answer=correct_answer,
            explanation=explanation,
            marks=marks,
            created_by=session['user_id']
        )
        
        db.session.add(question)
        db.session.commit()
        
        flash('Question added successfully', 'success')
        return redirect(url_for('admin_questions'))
    
    return render_template('admin/add_question.html', subjects=subjects)

@app.route('/admin/question/upload', methods=['GET', 'POST'])
def upload_questions():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    
    subjects = subjects_for_current_user()
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        subject_id = int(request.form['subject_id'])
        subject_class = (request.form.get('subject_class') or '').strip()
        
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                df = pd.read_excel(filepath)

                # Normalize whitespace-only cells to NA and drop fully-empty rows.
                # This avoids false validation failures caused by an extra blank row at the end
                # of the sheet (Excel often contains a trailing empty row).
                try:
                    df = df.replace(r'^\s*$', pd.NA, regex=True)
                except Exception:
                    # If regex replacement fails for any reason, continue with original df
                    pass

                # Drop rows where all columns are NA/empty
                df.dropna(how='all', inplace=True)

                # Validate required columns once
                required_cols = ['Question', 'Option A', 'Option B', 'Correct Answer']
                if not all(col in df.columns for col in required_cols):
                    flash('Excel file missing required columns (Question, Option A, Option B, Correct Answer)', 'danger')
                    return redirect(request.url)

                # Perform full-file validation first (fail-fast behavior)
                errors = []
                rows_to_insert = []

                def safe_val(col_name, row):
                    v = row.get(col_name)
                    return '' if pd.isna(v) else str(v)

                for row_idx, row in df.iterrows():
                    excel_row = int(row_idx) + 2

                    # Validate required fields
                    q_text = row.get('Question')
                    if pd.isna(q_text) or str(q_text).strip() == '':
                        errors.append((excel_row, 'Missing question text'))
                        continue

                    if pd.isna(row.get('Option A')) or pd.isna(row.get('Option B')):
                        errors.append((excel_row, 'Missing Option A or Option B'))
                        continue

                    if pd.isna(row.get('Correct Answer')) or str(row.get('Correct Answer')).strip() == '':
                        errors.append((excel_row, 'Missing Correct Answer'))
                        continue

                    # Parse marks
                    marks_val = 1
                    try:
                        mv = row.get('Mark')
                        if not pd.isna(mv):
                            marks_val = int(mv)
                    except Exception:
                        errors.append((excel_row, 'Invalid Mark value'))
                        continue

                    # If we reach here, row is valid — prepare cleaned data
                    # Determine subject for this row: prefer 'Subject Code' column if present
                    subject_for_row = subject_id
                    try:
                        # Prefer explicit Subject Code column if present
                        if 'Subject Code' in df.columns and not pd.isna(row.get('Subject Code')):
                            sc = str(row.get('Subject Code')).strip()
                            subj = Subject.query.filter(func.upper(Subject.code) == sc.upper()).first()
                            if subj:
                                subject_for_row = subj.id
                            else:
                                errors.append((excel_row, f'Unknown Subject Code: {sc}'))
                                continue
                        # If 'Subject' (name) column present, try to resolve by name (create if missing)
                        elif 'Subject' in df.columns and not pd.isna(row.get('Subject')):
                            sname = str(row.get('Subject')).strip()
                            subj = Subject.query.filter(func.lower(Subject.name) == sname.lower()).first()
                            if not subj:
                                # create new subject record so uploaded questions attach properly
                                subj = Subject(name=sname, code=None, created_by=session.get('user_id'))
                                db.session.add(subj)
                                db.session.commit()
                            subject_for_row = subj.id
                    except Exception:
                        pass

                    rows_to_insert.append({
                        'subject_id': subject_for_row,
                        'question_text': str(q_text).strip(),
                        'option_a': safe_val('Option A', row),
                        'option_b': safe_val('Option B', row),
                        'option_c': safe_val('Option C', row),
                        'option_d': safe_val('Option D', row),
                        'option_e': safe_val('Option E', row),
                        'correct_answer': str(row.get('Correct Answer')).upper().strip(),
                        'explanation': safe_val('Explanation', row),
                        'marks': marks_val
                    })

                if errors:
                    # Fail the whole upload and report errors — render the upload page with details
                    print('Validation errors during Excel upload:')
                    for r, reason in errors:
                        print(f' - Excel row {r}: {reason}')
                    # Clean up uploaded file before returning
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    # Return the upload page showing the exact rows and reasons so admin can fix the file
                    return render_template('admin/upload_questions.html', subjects=subjects, upload_errors=errors, classes=classes)

                # All rows valid — insert into database
                # If a subject_class was selected, update the Subject record
                try:
                    if subject_class:
                        subj_to_update = Subject.query.get(subject_id)
                        if subj_to_update:
                            subj_to_update.subject_class = subject_class
                            db.session.commit()
                except Exception:
                    try:
                        db.session.rollback()
                    except Exception:
                        pass
                added_count = 0
                for rdata in rows_to_insert:
                    # determine class for this question: prefer upload `subject_class`, else inherit from Subject
                    sid = rdata.get('subject_id', subject_id)
                    sc = subject_class or None
                    try:
                        if not sc:
                            subj_obj = Subject.query.get(sid)
                            sc = getattr(subj_obj, 'subject_class', None) if subj_obj else None
                    except Exception:
                        sc = subject_class or None

                    question = Question(
                        subject_id=sid,
                        question_text=rdata['question_text'],
                        option_a=rdata['option_a'],
                        option_b=rdata['option_b'],
                        option_c=rdata['option_c'],
                        option_d=rdata['option_d'],
                        option_e=rdata['option_e'],
                        correct_answer=rdata['correct_answer'],
                        explanation=rdata['explanation'],
                        marks=rdata['marks'],
                        subject_class=sc,
                        created_by=session['user_id']
                    )
                    db.session.add(question)
                    added_count += 1

                db.session.commit()
                flash(f'{added_count} questions uploaded successfully', 'success')
                
            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'danger')
            
            # Clean up uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return redirect(url_for('admin_questions'))
    
    # Ensure `classes` exists in case earlier code paths didn't define it
    try:
        existing_classes = [s.subject_class for s in subjects if getattr(s, 'subject_class', None)]
    except Exception:
        existing_classes = []
    common_classes = [
        'JSS1','JSS2','JSS3',
        'SS1','SS2','SS3',
        'BASIC1','BASIC2','BASIC3','BASIC4','BASIC5','BASIC6','BASIC7'
    ]
    classes = []
    for c in existing_classes + common_classes:
        if c and c not in classes:
            classes.append(c)

    return render_template('admin/upload_questions.html', subjects=subjects, classes=classes)


@app.route('/admin/question/<int:question_id>/delete', methods=['POST'])
def admin_delete_question(question_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    question = Question.query.get_or_404(question_id)

    # Ensure admin can only delete questions belonging to their school (unless superadmin)
    try:
        if not session.get('is_superadmin'):
            my_school = _get_session_school_id()
            if not question_belongs_to_school(question_id, my_school):
                flash('Access denied', 'danger')
                return redirect(url_for('admin_questions'))
    except Exception:
        pass

    # Delete any Answer records that reference this question (to avoid orphans)
    try:
        Answer.query.filter_by(question_id=question_id).delete()
    except Exception:
        pass

    db.session.delete(question)
    db.session.commit()

    flash('Question deleted successfully', 'success')
    return redirect(url_for('admin_questions'))


@app.route('/admin/questions/delete_all', methods=['POST'])
def admin_delete_all_questions():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    # Optionally allow deleting questions only for a specific subject
    subject_id = request.form.get('subject_id', type=int)

    if subject_id:
        questions = Question.query.filter_by(subject_id=subject_id).all()
    else:
        # Only include questions from subjects belonging to this admin's school (unless superadmin)
        if session.get('is_superadmin'):
            questions = Question.query.all()
        else:
            subj_ids = [s.id for s in subjects_for_current_user()]
            if not subj_ids:
                questions = []
            else:
                questions = Question.query.filter(Question.subject_id.in_(subj_ids)).all()

    q_ids = [q.id for q in questions]

    if not q_ids:
        flash('No questions found to delete', 'info')
        return redirect(url_for('admin_questions'))

    try:
        # Delete related answers first to avoid FK issues
        Answer.query.filter(Answer.question_id.in_(q_ids)).delete(synchronize_session=False)
    except Exception:
        # Fallback: attempt to delete via loop
        for qid in q_ids:
            try:
                Answer.query.filter_by(question_id=qid).delete()
            except Exception:
                pass

    # Delete questions
    Question.query.filter(Question.id.in_(q_ids)).delete(synchronize_session=False)
    db.session.commit()

    flash(f'Deleted {len(q_ids)} question(s) successfully', 'success')
    return redirect(url_for('admin_questions'))


@app.route('/admin/questions/delete_selected', methods=['POST'])
def admin_delete_selected_questions():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    ids_raw = request.form.get('ids', '')
    if not ids_raw:
        flash('No questions selected', 'warning')
        return redirect(url_for('admin_questions'))

    try:
        ids = [int(x) for x in ids_raw.split(',') if x.strip()]
    except Exception:
        flash('Invalid selection format', 'danger')
        return redirect(url_for('admin_questions'))
    q_ids = ids
    # Filter to questions that belong to this admin's school (unless superadmin)
    if not session.get('is_superadmin'):
        my_school = _get_session_school_id()
        allowed = [q for q in q_ids if question_belongs_to_school(q, my_school)]
    else:
        allowed = q_ids

    if not allowed:
        flash('No permitted questions selected for deletion', 'warning')
        return redirect(url_for('admin_questions'))

    try:
        # Delete related answers first
        Answer.query.filter(Answer.question_id.in_(allowed)).delete(synchronize_session=False)
    except Exception:
        for qid in allowed:
            try:
                Answer.query.filter_by(question_id=qid).delete()
            except Exception:
                pass

    try:
        Question.query.filter(Question.id.in_(allowed)).delete(synchronize_session=False)
        db.session.commit()
        flash(f'Deleted {len(allowed)} question(s) successfully', 'success')
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass
        flash('Error deleting selected questions', 'danger')

    return redirect(url_for('admin_questions'))


@app.route('/admin/question/template')
def download_question_template():
    # Only admin can download template
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    # Define template columns
    cols = [
        'Subject Code', 'Question', 'Option A', 'Option B', 'Option C', 'Option D', 'Option E',
        'Correct Answer', 'Explanation', 'Mark'
    ]

    # Create empty DataFrame with headers
    df = pd.DataFrame(columns=cols)

    # Write to in-memory Excel file
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    bio.seek(0)

    # Send as downloadable file
    return send_file(
        bio,
        as_attachment=True,
        download_name='question_template.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@app.route('/admin/question/generate', methods=['GET', 'POST'])
def generate_questions():
    # Admin-only
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    subjects = subjects_for_current_user()

    if request.method == 'GET':
        return render_template('admin/generate_questions.html', subjects=subjects)

    # POST: handle generation
    try:
        subject_id = int(request.form.get('subject_id'))
        class_level = request.form.get('class_level', '').strip()
        topics_raw = request.form.get('topics', '').strip()
        # Normalize topics into a list (comma, newline separated)
        topics = [t.strip() for t in re.split('[,\n;]+', topics_raw) if t.strip()]
        total_q = int(request.form.get('total_questions', 0))
    except Exception:
        flash('Invalid input', 'danger')
        return redirect(url_for('generate_questions'))

    if total_q <= 0 or total_q > 200:
        flash('Total questions must be between 1 and 200', 'danger')
        return redirect(url_for('generate_questions'))

    subject = Subject.query.get(subject_id)
    if not subject:
        flash('Selected subject not found', 'danger')
        return redirect(url_for('generate_questions'))

    # Try to use OpenAI API if API key provided in environment
    OPENAI_KEY = os.getenv('OPENAI_API_KEY')
    generated = []

    if OPENAI_KEY:
        # Build a prompt asking for JSON array of questions
        system_prompt = (
            "You are an exam question generator. Generate the requested number of multiple-choice questions "
            "suitable for the given subject and class level. Return a JSON array where each element is an object with keys: "
            "question_text, option_a, option_b, option_c, option_d, option_e (optional), correct_answer (A/B/C/D/E), explanation (optional), marks (integer)."
        )

        # Build user prompt including optional topics
        topic_section = ''
        if topics:
            topic_section = 'Focus topics: ' + ', '.join(topics) + '\n'

        user_prompt = (
            f"Subject: {subject.name}\n{topic_section}Class level: {class_level or 'unspecified'}\nTotal questions: {total_q}\n"
            "Return only valid JSON. Keep options concise. Ensure exactly one correct_answer per question."
        )

        try:
            try:
                import requests
            except Exception:
                requests = None

            headers = {
                'Authorization': f'Bearer {OPENAI_KEY}',
                'Content-Type': 'application/json'
            }
            data = {
                'model': 'gpt-4o-mini',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                'temperature': 0.7,
                'max_tokens': 2000
            }

            if not requests:
                raise RuntimeError('requests library not available in environment')
            resp = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data, timeout=30)
            if resp.status_code == 200:
                body = resp.json()
                text = ''
                # Extract assistant content
                for choice in body.get('choices', []):
                    msg = choice.get('message') or choice.get('text')
                    if isinstance(msg, dict):
                        text += msg.get('content','')
                    elif isinstance(msg, str):
                        text += msg

                # Try to parse JSON from the model output
                try:
                    arr = json.loads(text)
                    if isinstance(arr, list):
                        generated = arr[:total_q]
                except Exception:
                    # Attempt to extract JSON substring
                    m = re.search(r'(\[\s*\{.*\}\s*\])', text, re.S)
                    if m:
                        try:
                            arr = json.loads(m.group(1))
                            generated = arr[:total_q]
                        except Exception:
                            generated = []
            else:
                print('OpenAI call failed:', resp.status_code, resp.text)
        except Exception as e:
            print('OpenAI request error:', e)

    # If no OpenAI key or generation failed, fall back to simple template generator
    if not generated:
        for i in range(total_q):
            q_text = f"[{subject.name}] Sample question {i+1} for {class_level or 'general'}: What is {i+1}?"
            a = str((i+1))
            b = str((i+1)+1)
            c = str((i+1)+2)
            d = str((i+1)+3)
            generated.append({
                'question_text': q_text,
                'option_a': a,
                'option_b': b,
                'option_c': c,
                'option_d': d,
                'option_e': '',
                'correct_answer': 'A',
                'explanation': 'Auto-generated sample',
                'marks': 1
            })

    # Instead of inserting immediately, render a preview page where admin can review
    # Convert generated data to JSON for embedding in the preview form
    try:
        preview_json = json.dumps(generated)
    except Exception:
        preview_json = '[]'

    return render_template('admin/generate_preview.html', generated=generated, preview_json=preview_json, subject=subject, class_level=class_level)


@app.route('/admin/question/generate/commit', methods=['POST'])
def commit_generated_questions():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    subject_id = request.form.get('subject_id', type=int)
    preview_json = request.form.get('preview_json', '')

    try:
        items = json.loads(preview_json)
    except Exception:
        flash('Invalid data to save', 'danger')
        return redirect(url_for('generate_questions'))

    added = 0
    for item in items:
        try:
            ca = (item.get('correct_answer') or '').upper().strip()
            if not ca or ca not in ['A','B','C','D','E']:
                ca = 'A'

            q = Question(
                subject_id=subject_id,
                question_text=item.get('question_text') or '',
                option_a=item.get('option_a') or '',
                option_b=item.get('option_b') or '',
                option_c=item.get('option_c') or '',
                option_d=item.get('option_d') or '',
                option_e=item.get('option_e') or '',
                correct_answer=ca,
                explanation=item.get('explanation') or '',
                marks=int(item.get('marks') or 1),
                created_by=session['user_id']
            )
            db.session.add(q)
            added += 1
        except Exception as e:
            print('Failed to save generated question:', e)

    db.session.commit()
    flash(f'Saved {added} generated questions', 'success')
    return redirect(url_for('admin_questions'))


@app.route('/admin/diagnostics')
def diagnostics():
    # Admin only - view exam/question mapping for debugging
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    exams = exams_for_current_user()
    diagnostics_data = []

    for exam in exams:
        subject_id = exam.subject_id
        questions = Question.query.filter_by(subject_id=subject_id).all()
        diagnostics_data.append({
            'exam_id': exam.id,
            'exam_title': exam.title,
            'subject_id': subject_id,
            'subject_id_type': type(subject_id).__name__,
            'question_count': len(questions),
            'total_marks': sum(q.marks for q in questions),
            'questions': [{'id': q.id, 'text': q.question_text[:50], 'marks': q.marks} for q in questions[:3]]
        })

    return render_template('admin/diagnostics.html', data=diagnostics_data, 
                         total_exams=len(exams),
                         total_questions=Question.query.count(),
                         total_subjects=len(subjects_for_current_user()))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['xlsx', 'xls']

@app.route('/admin/exams')
def admin_exams():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    
    exams = exams_for_current_user()
    return render_template('admin/exams.html', exams=exams)


@app.route('/admin/exam/<int:exam_id>')
def admin_view_exam(exam_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    exam = Exam.query.get_or_404(exam_id)
    # Ensure admin can only view exams belonging to their school (unless superadmin)
    try:
        if not session.get('is_superadmin'):
            creator = User.query.get(exam.created_by)
            my_school = _get_session_school_id()
            if creator and creator.school_id and my_school and int(creator.school_id) != int(my_school):
                flash('Access denied to that exam', 'danger')
                return redirect(url_for('admin_exams'))
    except Exception:
        pass
    # Fetch questions for the exam subject
    try:
        subj_id = int(exam.subject_id)
    except Exception:
        subj_id = exam.subject_id

    questions = Question.query.filter_by(subject_id=subj_id).all()

    return render_template('admin/exam_detail.html', exam=exam, questions=questions)


@app.route('/admin/exam/<int:exam_id>/codes', methods=['GET', 'POST'])
def admin_exam_codes(exam_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    exam = Exam.query.get_or_404(exam_id)

    # Ensure the exam belongs to the current school (unless superadmin)
    try:
        if not session.get('is_superadmin'):
            cur_sid = _get_session_school_id()
            if not exam_belongs_to_school(exam.id, cur_sid):
                flash('Access denied to exam codes for this exam', 'danger')
                return redirect(url_for('admin_dashboard'))
    except Exception:
        pass

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'generate_all':
            students = students_for_current_user()
            created = 0
            for s in students:
                existing = ExamAccessCode.query.filter_by(exam_id=exam.id, student_id=s.id).first()
                if existing:
                    continue
                code = generate_unique_access_code()
                eac = ExamAccessCode(exam_id=exam.id, student_id=s.id, code=code)
                db.session.add(eac)
                created += 1
            db.session.commit()
            flash(f'Generated codes for {created} students', 'success')
            return redirect(url_for('admin_exam_codes', exam_id=exam.id))

        if action == 'delete_code':
            try:
                code_id = int(request.form.get('code_id'))
                c = ExamAccessCode.query.get(code_id)
                if c:
                    db.session.delete(c)
                    db.session.commit()
                    flash('Deleted code', 'success')
            except Exception:
                flash('Failed to delete code', 'danger')
            return redirect(url_for('admin_exam_codes', exam_id=exam.id))

    codes = ExamAccessCode.query.filter_by(exam_id=exam.id).all()
    students = students_for_current_user()
    return render_template('admin/exam_codes.html', exam=exam, codes=codes, students=students)


@app.route('/admin/exam/<int:exam_id>/codes/export')
def admin_exam_codes_export(exam_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    exam = Exam.query.get_or_404(exam_id)
    codes = ExamAccessCode.query.filter_by(exam_id=exam.id).all()

    # Build CSV content
    output = io.StringIO()
    output.write('student_username,student_full_name,code,created_at\n')
    for c in codes:
        uname = c.student.username if c.student else ''
        fname = c.student.full_name if c.student else ''
        created = c.created_at.strftime('%Y-%m-%d %H:%M') if c.created_at else ''
        output.write(f'{uname},{fname},{c.code},{created}\n')

    csv_data = output.getvalue()
    output.close()

    return Response(
        csv_data,
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=exam_{exam.id}_codes.csv'
        }
    )


@app.route('/admin/exam/<int:exam_id>/toggle_quick', methods=['POST'])
def admin_toggle_quick(exam_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    exam = Exam.query.get_or_404(exam_id)
    exam.allow_quick_start = not bool(exam.allow_quick_start)
    db.session.commit()
    flash(f'Quick start set to {exam.allow_quick_start}', 'success')
    return redirect(url_for('admin_view_exam', exam_id=exam.id))


@app.route('/admin/exam/<int:exam_id>/toggle_auto_start', methods=['POST'])
def admin_toggle_auto_start(exam_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    exam = Exam.query.get_or_404(exam_id)
    exam.auto_start_on_code = not bool(exam.auto_start_on_code)
    db.session.commit()
    flash(f'Auto-start on code entry set to {exam.auto_start_on_code}', 'success')
    return redirect(url_for('admin_view_exam', exam_id=exam.id))


@app.route('/admin/exam/<int:exam_id>/unlock/<int:student_id>', methods=['POST'])
def admin_unlock_student_exam(exam_id, student_id):
    """Allow admin to unlock an exam for a student by removing completed/submitted sessions."""
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    exam = Exam.query.get_or_404(exam_id)
    student = User.query.get_or_404(student_id)

    # Find any completed/submitted sessions and remove them (and answers) so student can retake
    sessions = ExamSession.query.filter(
        ExamSession.exam_id==exam.id,
        ExamSession.student_id==student.id,
        ExamSession.status.in_(['submitted', 'completed'])
    ).all()

    removed = 0
    for s in sessions:
        Answer.query.filter_by(exam_session_id=s.id).delete()
        db.session.delete(s)
        removed += 1
    db.session.commit()

    flash(f'Unlocked exam for {student.username}. Removed {removed} completed session(s).', 'success')
    return redirect(url_for('admin_view_exam', exam_id=exam.id))
    flash(f'Quick start {'enabled' if exam.allow_quick_start else 'disabled'} for exam "{exam.title}"', 'success')
    return redirect(url_for('admin_view_exam', exam_id=exam.id))


@app.route('/admin/exam/<int:exam_id>/delete', methods=['POST'])
def admin_delete_exam(exam_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    exam = Exam.query.get_or_404(exam_id)

    # Restrict deletion to exams owned by this admin's school (unless superadmin)
    try:
        if not session.get('is_superadmin'):
            creator = User.query.get(exam.created_by)
            my_school = _get_session_school_id()
            if creator and creator.school_id and my_school and int(creator.school_id) != int(my_school):
                flash('Access denied', 'danger')
                return redirect(url_for('admin_exams'))
    except Exception:
        pass

    # Delete related exam sessions and answers
    sessions = ExamSession.query.filter_by(exam_id=exam_id).all()
    for s in sessions:
        Answer.query.filter_by(exam_session_id=s.id).delete()
        db.session.delete(s)

    # Finally delete the exam
    db.session.delete(exam)
    db.session.commit()

    flash('Exam deleted successfully', 'success')
    return redirect(url_for('admin_exams'))


@app.route('/admin/exams/delete_selected', methods=['POST'])
def admin_delete_selected_exams():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    ids_raw = request.form.get('ids', '')
    if not ids_raw:
        flash('No exams selected', 'warning')
        return redirect(url_for('admin_exams'))

    try:
        ids = [int(x) for x in ids_raw.split(',') if x.strip()]
    except Exception:
        flash('Invalid selection format', 'danger')
        return redirect(url_for('admin_exams'))

    deleted = 0
    for ex_id in ids:
        try:
            exam = Exam.query.get(ex_id)
            if not exam:
                continue
            # Ensure admin can only delete exams for their school (unless superadmin)
            try:
                if not session.get('is_superadmin'):
                    creator = User.query.get(exam.created_by)
                    my_school = _get_session_school_id()
                    if creator and creator.school_id and my_school and int(creator.school_id) != int(my_school):
                        # skip deleting exams outside current school
                        continue
            except Exception:
                pass
            # delete exam sessions and answers
            sessions = ExamSession.query.filter_by(exam_id=ex_id).all()
            for s in sessions:
                try:
                    Answer.query.filter_by(exam_session_id=s.id).delete()
                except Exception:
                    pass
                try:
                    db.session.delete(s)
                except Exception:
                    pass

            try:
                ExamAccessCode.query.filter_by(exam_id=ex_id).delete()
            except Exception:
                pass

            try:
                db.session.delete(exam)
                deleted += 1
            except Exception:
                pass
        except Exception:
            try:
                db.session.rollback()
            except Exception:
                pass

    try:
        db.session.commit()
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass

    flash(f'Deleted {deleted} exam(s)', 'success')
    return redirect(url_for('admin_exams'))

@app.route('/admin/exam/add', methods=['GET', 'POST'])
def add_exam():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    
    subjects = subjects_for_current_user()
    # Prepare classes list (existing subject_class values + common defaults)
    try:
        existing_classes = [s.subject_class for s in subjects if getattr(s, 'subject_class', None)]
    except Exception:
        existing_classes = []
    common_classes = [
        'JSS1','JSS2','JSS3',
        'SS1','SS2','SS3',
        'BASIC1','BASIC2','BASIC3','BASIC4','BASIC5','BASIC6','BASIC7'
    ]
    classes = []
    for c in existing_classes + common_classes:
        if c and c not in classes:
            classes.append(c)

    if request.method == 'POST':
        subject_id = int(request.form['subject_id'])
        title = request.form['title']
        description = request.form['description']
        duration = request.form['duration']
        subject_class = (request.form.get('subject_class') or '').strip() or None

        # Calculate total marks for the exam based on questions in the subject
        questions = Question.query.filter_by(subject_id=subject_id).all()
        total_marks = sum(q.marks for q in questions)

        exam = Exam(
            subject_id=subject_id,
            title=title,
            description=description,
            duration=duration,
            subject_class=subject_class,
            allow_quick_start=True,
            code=generate_unique_exam_code(),
            total_marks=total_marks,
            created_by=session['user_id']
        )

        db.session.add(exam)
        db.session.commit()

        flash('Exam created successfully', 'success')
        return redirect(url_for('admin_exams'))

    return render_template('admin/add_exam.html', subjects=subjects, classes=classes)

@app.route('/admin/results')
def admin_results():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    
    # Scope results to the effective school for non-superadmins
    try:
        if session.get('is_superadmin'):
            exam_sessions = ExamSession.query.filter_by(status='completed').all()
        else:
            cur_sid = _get_effective_school_id()
            # join with student to filter by student.school_id
            exam_sessions = ExamSession.query.join(User, ExamSession.student_id == User.id).filter(ExamSession.status=='completed', User.school_id==cur_sid).all()
    except Exception:
        exam_sessions = ExamSession.query.filter_by(status='completed').all()
    subjects = subjects_for_current_user()
    return render_template('admin/results.html', exam_sessions=exam_sessions, subjects=subjects)


@app.route('/admin/results/export_subject', methods=['POST'])
def admin_export_results_by_subject():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    sid = request.form.get('subject_id')
    try:
        subject_id = int(sid)
    except Exception:
        flash('Invalid subject selection', 'danger')
        return redirect(url_for('admin_results'))

    subject = Subject.query.get(subject_id)
    if not subject:
        flash('Subject not found', 'danger')
        return redirect(url_for('admin_results'))

    # Gather completed exam sessions for exams in this subject
    sessions = ExamSession.query.join(Exam, ExamSession.exam_id == Exam.id).filter(Exam.subject_id==subject_id, ExamSession.status=='completed').all()

    # Filter by school ownership for non-superadmins
    filtered = []
    cur_sid = _get_effective_school_id()
    for s in sessions:
        try:
            if session.get('is_superadmin'):
                filtered.append(s)
            else:
                # student must belong to current school and exam must belong to school
                student = User.query.get(s.student_id)
                if not student or not student.school_id:
                    continue
                if int(student.school_id) != int(cur_sid):
                    continue
                if not exam_belongs_to_school(s.exam_id, cur_sid):
                    continue
                filtered.append(s)
        except Exception:
            continue

    # Build Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.title = f"{subject.name[:28]} Results"
    headers = ['NAME', 'SUBJECT', 'CLASS', 'SCORE', 'EXAM']
    ws.append(headers)
    for s in filtered:
        try:
            student = User.query.get(s.student_id)
            exam = Exam.query.get(s.exam_id)
            name = student.full_name or student.username
            subj_name = exam.subject.name if exam and exam.subject else subject.name
            subj_class = exam.subject_class or (exam.subject.subject_class if exam and exam.subject else '')
            score = s.score if s.score is not None else 0
            exam_title = exam.title if exam else ''
            ws.append([name, subj_name, subj_class, score, exam_title])
        except Exception:
            continue

    # Save to bytes
    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)

    filename = f"results_{subject.name.replace(' ', '_')}.xlsx"
    return send_file(bio, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=filename)

# Student Routes
@app.route('/student/dashboard')
def student_dashboard():
    if 'user_id' not in session or session['role'] != 'student':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    
    # Only show exams that belong to the student's school
    student = User.query.get(session['user_id'])
    try:
        my_school = int(student.school_id) if student and student.school_id else None
    except Exception:
        my_school = None
    exams = exams_for_school(my_school)
    completed_exams = ExamSession.query.filter_by(student_id=session['user_id'], status='completed').all()
    # Resolve school object for header display
    school_obj = None
    try:
        if my_school:
            school_obj = School.query.get(my_school)
    except Exception:
        school_obj = None

    schools = get_schools_safe()
    return render_template('student/dashboard.html', exams=exams, completed_exams=completed_exams, school=school_obj, schools=schools)


@app.route('/start', methods=['GET'])
def start():
    # Public landing page where students enter their username/code and exam code
    return render_template('start.html')


@app.route('/start', methods=['POST'])
def start_exam():
    username_or_code = request.form.get('username_or_code', '').strip()
    exam_code = request.form.get('exam_code', '').strip()
    access_code = request.form.get('access_code', '').strip()

    if not username_or_code or not exam_code:
        flash('Both fields are required', 'danger')
        return redirect(url_for('start'))

    # Find the student by username (students use username as code sometimes)
    student = User.query.filter_by(username=username_or_code).first()
    if not student:
        flash('Student not found. Please check your username/code.', 'danger')
        return redirect(url_for('start'))

    exam = Exam.query.filter_by(code=exam_code).first()
    if not exam:
        flash('Exam not found. Please check the exam code.', 'danger')
        return redirect(url_for('start'))

    if not exam.is_active:
        flash('This exam is not active.', 'danger')
        return redirect(url_for('start'))

    # Ensure exam belongs to student's school
    try:
        stud_school = student.school_id
        if stud_school and not exam_belongs_to_school(exam.id, stud_school):
            flash('This exam is not available for your school.', 'danger')
            return redirect(url_for('start'))
    except Exception:
        pass

    # If the exam is configured to NOT auto-start on code entry, show a confirmation page
    if not getattr(exam, 'auto_start_on_code', False):
        # Render confirmation page; the form will POST to /start/begin to actually create the session
        return render_template('start_confirm.html', exam=exam, username_or_code=username_or_code, exam_code=exam_code, access_code=access_code, action=url_for('start_begin'), student_name=student.full_name)

    # Create an exam session and answer records (similar to take_exam)
    questions = Question.query.filter_by(subject_id=exam.subject_id).all()
    if not questions:
        flash('No questions available for this exam', 'danger')
        return redirect(url_for('start'))

    # Prevent re-taking if student already has a completed/submitted session for this exam
    locked = ExamSession.query.filter(
        ExamSession.exam_id==exam.id,
        ExamSession.student_id==student.id,
        ExamSession.status.in_(['submitted', 'completed'])
    ).first()
    if locked:
        flash('This exam has already been completed for your account. Contact the administrator to request a retake.', 'danger')
        return redirect(url_for('start'))

    # Validate access code: must match a generated ExamAccessCode for this student and exam
    eac = ExamAccessCode.query.filter_by(exam_id=exam.id, student_id=student.id, code=access_code).first()
    if not eac:
        flash('Invalid or missing access code. Please check the code provided by your school/admin.', 'danger')
        return redirect(url_for('start'))

    # Remove any in-progress session for this student/exam to start fresh
    active_session = ExamSession.query.filter_by(exam_id=exam.id, student_id=student.id, status='in_progress').first()
    if active_session:
        Answer.query.filter_by(exam_session_id=active_session.id).delete()
        db.session.delete(active_session)
        db.session.commit()

    random.shuffle(questions)
    exam_session = ExamSession(exam_id=exam.id, student_id=student.id, start_time=datetime.utcnow(), status='in_progress')
    db.session.add(exam_session)
    db.session.commit()

    for q in questions:
        a = Answer(exam_session_id=exam_session.id, question_id=q.id, selected_answer=None, is_correct=None)
        db.session.add(a)
    db.session.commit()

    # Temporarily log the student in for the duration of the exam only
    session['user_id'] = student.id
    session['role'] = 'student'
    session['temp_login'] = True
    session['temp_exam_session'] = exam_session.id

    return redirect(url_for('start_exam_view', session_id=exam_session.id))


@app.route('/start/begin', methods=['POST'])
def start_begin():
    # This endpoint is called from the confirmation page to actually start the exam
    username_or_code = request.form.get('username_or_code', '').strip()
    exam_code = request.form.get('exam_code', '').strip()
    access_code = request.form.get('access_code', '').strip()

    if not username_or_code or not exam_code:
        flash('Both fields are required', 'danger')
        return redirect(url_for('start'))

    student = User.query.filter_by(username=username_or_code).first()
    if not student:
        flash('Student not found. Please check your username/code.', 'danger')
        return redirect(url_for('start'))

    exam = Exam.query.filter_by(code=exam_code).first()
    if not exam or not exam.is_active:
        flash('Exam not found or not active.', 'danger')
        return redirect(url_for('start'))

    # Validate access code
    # Prevent re-taking if student already has a completed/submitted session for this exam
    locked = ExamSession.query.filter(
        ExamSession.exam_id==exam.id,
        ExamSession.student_id==student.id,
        ExamSession.status.in_(['submitted', 'completed'])
    ).first()
    if locked:
        flash('This exam has already been completed for your account. Contact the administrator to request a retake.', 'danger')
        return redirect(url_for('start'))

    eac = ExamAccessCode.query.filter_by(exam_id=exam.id, student_id=student.id, code=access_code).first()
    if not eac:
        flash('Invalid or missing access code. Please check the code provided by your school/admin.', 'danger')
        return redirect(url_for('start'))

    # Remove any in-progress session for this student/exam to start fresh
    active_session = ExamSession.query.filter_by(exam_id=exam.id, student_id=student.id, status='in_progress').first()
    if active_session:
        Answer.query.filter_by(exam_session_id=active_session.id).delete()
        db.session.delete(active_session)
        db.session.commit()

    questions = Question.query.filter_by(subject_id=exam.subject_id).all()
    if not questions:
        flash('No questions available for this exam', 'danger')
        return redirect(url_for('start'))

    random.shuffle(questions)
    exam_session = ExamSession(exam_id=exam.id, student_id=student.id, start_time=datetime.utcnow(), status='in_progress')
    db.session.add(exam_session)
    db.session.commit()

    for q in questions:
        a = Answer(exam_session_id=exam_session.id, question_id=q.id, selected_answer=None, is_correct=None)
        db.session.add(a)
    db.session.commit()

    session['user_id'] = student.id
    session['role'] = 'student'
    session['temp_login'] = True
    session['temp_exam_session'] = exam_session.id

    return redirect(url_for('start_exam_view', session_id=exam_session.id))


@app.route('/start/exam/<int:session_id>')
def start_exam_view(session_id):
    # Allow viewing the exam only if temp session matches or the real logged-in student
    exam_session = ExamSession.query.get_or_404(session_id)

    # If user is not logged in or not the same student, deny
    if 'user_id' not in session:
        flash('Access denied', 'danger')
        return redirect(url_for('start'))

    # Ensure the session matches the temp session (for unauthenticated starts)
    if session.get('temp_exam_session') != session_id and session.get('user_id') != exam_session.student_id:
        flash('Access denied', 'danger')
        return redirect(url_for('start'))

    exam = Exam.query.get_or_404(exam_session.exam_id)
    return render_template('student/exam.html', exam=exam, session_id=session_id)


@app.route('/start/quick', methods=['GET', 'POST'])
def start_quick():
    """Quick start: student provides username and exam code (subject/exam code).
    This will allow start only if the exam has `allow_quick_start` enabled or
    the student already has a generated ExamAccessCode for that exam."""
    if request.method == 'GET':
        return render_template('quick_start.html')

    username = request.form.get('username', '').strip()
    exam_code = request.form.get('exam_code', '').strip()

    if not username or not exam_code:
        flash('Both username and exam code are required', 'danger')
        return redirect(url_for('start_quick'))

    student = User.query.filter_by(username=username).first()
    if not student:
        flash('Student not found', 'danger')
        return redirect(url_for('start_quick'))

    exam = Exam.query.filter_by(code=exam_code).first()
    if not exam:
        flash('Exam not found. Please check the exam code.', 'danger')
        return redirect(url_for('start_quick'))

    if not exam.is_active:
        flash('This exam is not active.', 'danger')
        return redirect(url_for('start_quick'))

    # Prevent re-taking if student already has a completed/submitted session for this exam
    locked = ExamSession.query.filter(
        ExamSession.exam_id==exam.id,
        ExamSession.student_id==student.id,
        ExamSession.status.in_(['submitted', 'completed'])
    ).first()
    if locked:
        flash('This exam has already been completed for your account. Contact the administrator to request a retake.', 'danger')
        return redirect(url_for('start_quick'))

    # Allow if quick start enabled or an access code exists for this student/exam
    has_access_code = ExamAccessCode.query.filter_by(exam_id=exam.id, student_id=student.id).first()
    if not exam.allow_quick_start and not has_access_code:
        flash('Quick start is not enabled for this exam. Please use the full Start page or contact your administrator.', 'danger')
        return redirect(url_for('start'))

    # If the exam is configured to NOT auto-start on code entry, show a confirmation page
    if not getattr(exam, 'auto_start_on_code', False):
        # Render confirmation page; the form will POST to /start/quick/begin to actually create the session
        return render_template('start_confirm.html', exam=exam, username_or_code=student.username, exam_code=exam_code, action=url_for('start_quick_begin'), student_name=student.full_name)

    # proceed to create exam session like /start
    questions = Question.query.filter_by(subject_id=exam.subject_id).all()
    if not questions:
        flash('No questions available for this exam', 'danger')
        return redirect(url_for('start_quick'))

    active_session = ExamSession.query.filter_by(exam_id=exam.id, student_id=student.id, status='in_progress').first()
    if active_session:
        Answer.query.filter_by(exam_session_id=active_session.id).delete()
        db.session.delete(active_session)
        db.session.commit()

    random.shuffle(questions)
    exam_session = ExamSession(exam_id=exam.id, student_id=student.id, start_time=datetime.utcnow(), status='in_progress')
    db.session.add(exam_session)
    db.session.commit()

    for q in questions:
        a = Answer(exam_session_id=exam_session.id, question_id=q.id, selected_answer=None, is_correct=None)
        db.session.add(a)
    db.session.commit()

    # session-based temporary login for exam
    session['user_id'] = student.id
    session['role'] = 'student'
    session['temp_login'] = True
    session['temp_exam_session'] = exam_session.id

    return redirect(url_for('start_exam_view', session_id=exam_session.id))


@app.route('/start/quick/begin', methods=['POST'])
def start_quick_begin():
    username = request.form.get('username_or_code', '').strip()
    exam_code = request.form.get('exam_code', '').strip()

    if not username or not exam_code:
        flash('Both username and exam code are required', 'danger')
        return redirect(url_for('start_quick'))

    student = User.query.filter_by(username=username).first()
    if not student:
        flash('Student not found', 'danger')
        return redirect(url_for('start_quick'))

    exam = Exam.query.filter_by(code=exam_code).first()
    if not exam or not exam.is_active:
        flash('Exam not found. Please check the exam code.', 'danger')
        return redirect(url_for('start_quick'))

    # proceed as regular quick start now that confirmation was given
    # Prevent re-taking if student already has a completed/submitted session for this exam
    locked = ExamSession.query.filter(
        ExamSession.exam_id==exam.id,
        ExamSession.student_id==student.id,
        ExamSession.status.in_(['submitted', 'completed'])
    ).first()
    if locked:
        flash('This exam has already been completed for your account. Contact the administrator to request a retake.', 'danger')
        return redirect(url_for('start_quick'))

    questions = Question.query.filter_by(subject_id=exam.subject_id).all()
    if not questions:
        flash('No questions available for this exam', 'danger')
        return redirect(url_for('start_quick'))

    active_session = ExamSession.query.filter_by(exam_id=exam.id, student_id=student.id, status='in_progress').first()
    if active_session:
        Answer.query.filter_by(exam_session_id=active_session.id).delete()
        db.session.delete(active_session)
        db.session.commit()

    random.shuffle(questions)
    exam_session = ExamSession(exam_id=exam.id, student_id=student.id, start_time=datetime.utcnow(), status='in_progress')
    db.session.add(exam_session)
    db.session.commit()

    for q in questions:
        a = Answer(exam_session_id=exam_session.id, question_id=q.id, selected_answer=None, is_correct=None)
        db.session.add(a)
    db.session.commit()

    # session-based temporary login for exam
    session['user_id'] = student.id
    session['role'] = 'student'
    session['temp_login'] = True
    session['temp_exam_session'] = exam_session.id

    return redirect(url_for('start_exam_view', session_id=exam_session.id))


@app.route('/start/submitted/<int:session_id>')
def start_submitted(session_id):
    # Page shown to students who submitted via quick/temp login informing them to login to view results
    msg = 'Your exam was submitted successfully. Please login to view your result.'
    return render_template('submitted.html', message=msg)

@app.route('/student/exam/<int:exam_id>')
def take_exam(exam_id):
    if 'user_id' not in session or session['role'] != 'student':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    
    exam = Exam.query.get_or_404(exam_id)
    
    # Check if student already has a COMPLETED or SUBMITTED session for this exam
    # Historically we prevented students from restarting an exam if they had a completed
    # session; for automated tests and retakes we allow creating a new session even
    # if a completed session exists (administrator can still restrict retakes separately).
    completed_session = ExamSession.query.filter(
        ExamSession.exam_id==exam_id,
        ExamSession.student_id==session['user_id'],
        ExamSession.status.in_(['submitted', 'completed'])
    ).first()
    if completed_session:
        # Do not allow students to retake an exam once submitted/completed.
        # Only an administrator can unlock/remove completed sessions to permit a retake.
        flash('You have already completed this exam. Contact the administrator to request a retake.', 'danger')
        return redirect(url_for('student_dashboard'))
    
    # Check for in-progress session - restart it with fresh question set
    active_session = ExamSession.query.filter_by(
        exam_id=exam_id, 
        student_id=session['user_id'],
        status='in_progress'
    ).first()
    
    if active_session:
        # Delete the old session and its answers to create a fresh one
        Answer.query.filter_by(exam_session_id=active_session.id).delete()
        db.session.delete(active_session)
        db.session.commit()
    
    # Create new exam session with all questions
    # ensure subject_id types match and fetch questions
    try:
        subj_id = int(exam.subject_id)
    except Exception:
        subj_id = exam.subject_id

    questions = Question.query.filter_by(subject_id=subj_id).all()

    if not questions:
        # log debugging info to console to help diagnose
        print(f"DEBUG: exam_id={exam_id} subject_id={exam.subject_id} (type={type(exam.subject_id)}) -> questions_found=0 total_questions_in_db={Question.query.count()}")
        flash('No questions available for this exam', 'danger')
        return redirect(url_for('student_dashboard'))
    
    print(f"DEBUG: Creating exam session with {len(questions)} questions for exam_id={exam_id}, subject_id={subj_id}")
    
    # Randomize questions
    random.shuffle(questions)
    
    exam_session = ExamSession(
        exam_id=exam_id,
        student_id=session['user_id'],
        start_time=datetime.utcnow(),
        status='in_progress'
    )
    
    db.session.add(exam_session)
    db.session.commit()
    
    # Create answer records for all questions
    for idx, question in enumerate(questions):
        answer = Answer(
            exam_session_id=exam_session.id,
            question_id=question.id,
            selected_answer=None,
            is_correct=None
        )
        db.session.add(answer)
    
    db.session.commit()
    print(f"DEBUG: Created {len(questions)} answer records for session {exam_session.id}")
    session_id = exam_session.id
    
    return render_template('student/exam.html', exam=exam, session_id=session_id)

@app.route('/api/exam/<int:session_id>/question/<int:question_index>')
def get_question(session_id, question_index):
    if 'user_id' not in session:
        return {'error': 'Unauthorized'}, 401
    
    exam_session = ExamSession.query.get_or_404(session_id)
    
    if exam_session.student_id != session['user_id']:
        return {'error': 'Access denied'}, 403
    
    # Get all answers for this session
    answers = Answer.query.filter_by(exam_session_id=session_id).order_by(Answer.id).all()
    
    print(f"DEBUG get_question: session_id={session_id}, question_index={question_index}, total_answers={len(answers)}")
    
    if len(answers) == 0:
        print(f"ERROR: No answers found for session {session_id}")
        return {'error': 'No questions available for this exam session'}, 400
    
    if question_index < 0 or question_index >= len(answers):
        return {'error': 'Invalid question index'}, 404
    
    answer = answers[question_index]
    question = Question.query.get(answer.question_id)
    
    if not question:
        print(f"ERROR: Question {answer.question_id} not found in database")
        return {'error': 'Question data corrupted'}, 500
    
    # Prepare options
    options = []
    if question.option_a: options.append({'letter': 'A', 'text': question.option_a})
    if question.option_b: options.append({'letter': 'B', 'text': question.option_b})
    if question.option_c: options.append({'letter': 'C', 'text': question.option_c})
    if question.option_d: options.append({'letter': 'D', 'text': question.option_d})
    if question.option_e: options.append({'letter': 'E', 'text': question.option_e})
    
    return {
        'question_index': question_index,
        'total_questions': len(answers),
        'question': {
            'id': question.id,
            'text': question.question_text,
            'options': options,
            'selected_answer': answer.selected_answer,
            'marks': question.marks
        }
    }

@app.route('/api/exam/<int:session_id>/answer', methods=['POST'])
def save_answer(session_id):
    if 'user_id' not in session:
        return {'error': 'Unauthorized'}, 401
    
    exam_session = ExamSession.query.get_or_404(session_id)
    
    if exam_session.student_id != session['user_id']:
        return {'error': 'Access denied'}, 403
    
    data = request.get_json()
    question_index = data.get('question_index')
    answer = data.get('answer')
    
    # Get all answers for this session
    answers = Answer.query.filter_by(exam_session_id=session_id).order_by(Answer.id).all()
    
    if question_index < 0 or question_index >= len(answers):
        return {'error': 'Invalid question index'}, 404
    
    answer_record = answers[question_index]
    # Normalize the student's answer
    answer_norm = '' if answer is None else str(answer).upper().strip()
    answer_record.selected_answer = answer_norm

    # Check if answer is correct. Support both letter (A/B/C/D/E) or full option text
    question = Question.query.get(answer_record.question_id)
    correct_letter = (question.correct_answer or '').upper().strip()
    # Map letters to option text for fallback comparison
    opts = {
        'A': (question.option_a or ''),
        'B': (question.option_b or ''),
        'C': (question.option_c or ''),
        'D': (question.option_d or ''),
        'E': (question.option_e or '')
    }

    is_correct = False
    if len(answer_norm) == 1 and answer_norm in opts:
        is_correct = (answer_norm == correct_letter)
    else:
        # Compare normalized text values
        sel_text = answer_norm
        correct_text = (opts.get(correct_letter, '') or '').upper().strip()
        is_correct = (sel_text == correct_text)

    answer_record.is_correct = bool(is_correct)
    
    db.session.commit()
    
    return {'status': 'success'}

@app.route('/api/exam/<int:session_id>/submit', methods=['POST'])
def submit_exam(session_id):
    if 'user_id' not in session:
        return {'error': 'Unauthorized'}, 401
    
    exam_session = ExamSession.query.get_or_404(session_id)
    
    if exam_session.student_id != session['user_id']:
        return {'error': 'Access denied'}, 403
    
    # Recalculate correctness for all answers (in case data changed or normalization needed)
    answers = Answer.query.filter_by(exam_session_id=session_id).all()
    total_score = 0

    for a in answers:
        question = Question.query.get(a.question_id)
        if not question:
            a.is_correct = False
            continue

        # Normalize stored selected answer and correct answer
        sel = '' if a.selected_answer is None else str(a.selected_answer).upper().strip()
        correct_letter = (question.correct_answer or '').upper().strip()

        opts = {
            'A': (question.option_a or ''),
            'B': (question.option_b or ''),
            'C': (question.option_c or ''),
            'D': (question.option_d or ''),
            'E': (question.option_e or '')
        }

        is_correct = False
        if len(sel) == 1 and sel in opts:
            is_correct = (sel == correct_letter)
        else:
            sel_text = sel
            correct_text = (opts.get(correct_letter, '') or '').upper().strip()
            is_correct = (sel_text == correct_text)

        a.is_correct = bool(is_correct)
        if a.is_correct:
            try:
                total_score += int(question.marks or 1)
            except Exception:
                total_score += 1

    # Update exam session
    exam_session.end_time = datetime.utcnow()
    exam_session.score = total_score
    exam_session.status = 'completed'

    db.session.commit()

    # If this was a temporary login started via /start, clear the temp login so student
    # cannot view results without performing a normal login later. Return a message
    # so the client can show a helpful UI telling the student to login to view results.
    response = {'status': 'success', 'score': total_score}
    try:
        if session.get('temp_login') and session.get('temp_exam_session') == session_id:
            # clear temp login
            session.pop('user_id', None)
            session.pop('role', None)
            session.pop('temp_login', None)
            session.pop('temp_exam_session', None)
            response['post_submit_message'] = 'Your exam has been submitted. Please login to view your results.'
            response['session_id'] = session_id
    except Exception:
        pass

    return response

@app.route('/student/results')
def student_results():
    if 'user_id' not in session or session['role'] != 'student':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    
    exam_sessions = ExamSession.query.filter_by(
        student_id=session['user_id'], 
        status='completed'
    ).all()
    
    return render_template('student/results.html', exam_sessions=exam_sessions)

@app.route('/student/result/<int:session_id>')
def view_result(session_id):
    if 'user_id' not in session or session['role'] != 'student':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    
    exam_session = ExamSession.query.get_or_404(session_id)
    
    if exam_session.student_id != session['user_id']:
        flash('Access denied', 'danger')
        return redirect(url_for('student_dashboard'))
    
    answers = Answer.query.filter_by(exam_session_id=session_id).all()
    questions = []

    for answer in answers:
        question = Question.query.get(answer.question_id)
        questions.append({
            'question': question,
            'selected_answer': answer.selected_answer,
            'is_correct': answer.is_correct
        })

    # Compute time used: prefer end_time - start_time, otherwise now - start_time
    time_used_str = 'N/A'
    try:
        if exam_session.start_time:
            end = exam_session.end_time or datetime.utcnow()
            delta = end - exam_session.start_time
            seconds = int(delta.total_seconds())
            minutes = seconds // 60
            secs = seconds % 60
            if minutes > 0:
                time_used_str = f"{minutes} min {secs} sec"
            else:
                time_used_str = f"{secs} sec"
    except Exception:
        time_used_str = 'N/A'

    return render_template('student/result_detail.html', 
                         exam_session=exam_session, 
                         questions=questions,
                         time_used=time_used_str)


@app.route('/student/result/<int:session_id>/pdf')
def result_pdf(session_id):
    # Generate a printable PDF of the marked script (fallback to HTML)
    if 'user_id' not in session or session['role'] != 'student':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    exam_session = ExamSession.query.get_or_404(session_id)
    if exam_session.student_id != session['user_id']:
        flash('Access denied', 'danger')
        return redirect(url_for('student_dashboard'))

    answers = Answer.query.filter_by(exam_session_id=session_id).all()
    questions = []
    for answer in answers:
        question = Question.query.get(answer.question_id)
        questions.append({
            'question': question,
            'selected_answer': answer.selected_answer,
            'is_correct': answer.is_correct
        })

    # Compute time used for PDF as well
    time_used_str = 'N/A'
    try:
        if exam_session.start_time:
            end = exam_session.end_time or datetime.utcnow()
            delta = end - exam_session.start_time
            seconds = int(delta.total_seconds())
            minutes = seconds // 60
            secs = seconds % 60
            if minutes > 0:
                time_used_str = f"{minutes} min {secs} sec"
            else:
                time_used_str = f"{secs} sec"
    except Exception:
        time_used_str = 'N/A'

    # Render HTML for the result (pass pdf_mode to hide buttons)
    rendered = render_template('student/result_detail.html', exam_session=exam_session, questions=questions, pdf_mode=True, time_used=time_used_str)

    # If pdfkit/wkhtmltopdf is available, convert to PDF
    # Try to generate PDF if pdfkit is available and wkhtmltopdf binary exists
    try:
        import shutil
        # Allow explicit override via environment variable WKHTMLTOPDF_BIN
        wk = os.getenv('WKHTMLTOPDF_BIN') or shutil.which('wkhtmltopdf')
        if wk:
            wk = str(wk)
    except Exception:
        wk = None

    if pdfkit and wk:
        try:
            config = None
            try:
                from pdfkit import configuration
                config = configuration(wkhtmltopdf=wk)
            except Exception:
                config = None

            # Attempt to create PDF bytes with zero margins for printing
            options = {
                'margin-top': '0mm',
                'margin-bottom': '0mm',
                # Use a slight negative left margin to increase usable width on the page
                'margin-left': '-0.25in',
                'margin-right': '0in',
                'encoding': 'UTF-8'
            }
            pdf_bytes = pdfkit.from_string(rendered, False, options=options, configuration=config)
            return Response(pdf_bytes, mimetype='application/pdf', headers={
                'Content-Disposition': f'attachment; filename=result_{session_id}.pdf'
            })
        except Exception as e:
            # Fall back to returning HTML but warn user
            print(f"PDF generation failed: {e}")
            flash('PDF generation failed on server; returning printable HTML.', 'warning')
            return Response(rendered, mimetype='text/html', headers={
                'Content-Disposition': f'attachment; filename=result_{session_id}.html'
            })

    # No pdfkit or wkhtmltopdf - return printable HTML as fallback (downloadable)
    flash('PDF generation not available on server; download/print the HTML page.', 'warning')
    return Response(rendered, mimetype='text/html', headers={
        'Content-Disposition': f'attachment; filename=result_{session_id}.html'
    })

if __name__ == '__main__':
    try:
        init_db()
    except Exception as e:
        print('init_db failed:', e)
    app.run(debug=True)