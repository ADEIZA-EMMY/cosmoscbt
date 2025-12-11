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
# Optional HTTP client for AI integration
import json
import re
#from gunicorn.app.base import Application

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cbt.db'
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
    duration = db.Column(db.Integer, nullable=False)  # in minutes
    total_marks = db.Column(db.Integer, nullable=False)
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


def generate_unique_exam_code(attempts=10):
    """Generate a unique six-digit numeric code for an exam."""
    for _ in range(attempts):
        code = '{:06d}'.format(random.randint(0, 999999))
        if not Exam.query.filter_by(code=code).first():
            return code
    # Fallback: deterministic based on timestamp
    return datetime.utcnow().strftime('%H%M%S')

# Create database tables
with app.app_context():
    db.create_all()
    # Ensure `code` column exists on existing installations (SQLite supports ADD COLUMN)
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('exam')]
        if 'code' not in columns:
            # Add column to existing table; SQLite will accept ADD COLUMN
            db.engine.execute('ALTER TABLE exam ADD COLUMN code VARCHAR(6)')
            print('Added `code` column to exam table')
    except Exception:
        # If inspector or ALTER fails, skip — new installs will have column from model
        pass
    
    # Create default admin user if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', role='admin', full_name='System Administrator')
        admin.set_password('admin123')
        db.session.add(admin)
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
    
    existing_subjects = Subject.query.count()
    if existing_subjects == 0:
        admin_user = User.query.filter_by(username='admin').first()
        admin_id = admin_user.id if admin_user else None
        for subject_name, description in NIGERIAN_SUBJECTS:
            if not Subject.query.filter_by(name=subject_name).first():
                subject = Subject(name=subject_name, description=description, created_by=admin_id)
                db.session.add(subject)
        db.session.commit()
        print(f"Seeded {len(NIGERIAN_SUBJECTS)} Nigerian subjects.")

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
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['full_name'] = user.full_name
            
            flash('Login successful!', 'success')
            
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']
        role = 'student'  # Only student registration is allowed
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('register.html')
        
        user = User(username=username, full_name=full_name, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirectpython(url_for('login'))
    
    return render_template('register.html')

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
    
    subjects = Subject.query.all()
    exams = Exam.query.all()
    students = User.query.filter_by(role='student').all()
    
    return render_template('admin/dashboard.html', subjects=subjects, exams=exams, students=students)

@app.route('/admin/subjects')
def admin_subjects():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    
    subjects = Subject.query.all()
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


@app.route('/admin/students')
def admin_students():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    students = User.query.filter_by(role='student').all()
    return render_template('admin/students.html', students=students)


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

@app.route('/admin/questions')
def admin_questions():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    
    subject_id = request.args.get('subject_id', type=int)
    questions = Question.query
    
    if subject_id:
        questions = questions.filter_by(subject_id=subject_id)
    
    questions = questions.all()
    subjects = Subject.query.all()
    
    return render_template('admin/questions.html', questions=questions, subjects=subjects, selected_subject=subject_id)

@app.route('/admin/question/add', methods=['GET', 'POST'])
def add_question():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    
    subjects = Subject.query.all()
    
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
    
    subjects = Subject.query.all()
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        subject_id = int(request.form['subject_id'])
        
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
                    rows_to_insert.append({
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
                    return render_template('admin/upload_questions.html', subjects=subjects, upload_errors=errors)

                # All rows valid — insert into database
                added_count = 0
                for rdata in rows_to_insert:
                    question = Question(
                        subject_id=subject_id,
                        question_text=rdata['question_text'],
                        option_a=rdata['option_a'],
                        option_b=rdata['option_b'],
                        option_c=rdata['option_c'],
                        option_d=rdata['option_d'],
                        option_e=rdata['option_e'],
                        correct_answer=rdata['correct_answer'],
                        explanation=rdata['explanation'],
                        marks=rdata['marks'],
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
    
    return render_template('admin/upload_questions.html', subjects=subjects)


@app.route('/admin/question/<int:question_id>/delete', methods=['POST'])
def admin_delete_question(question_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    question = Question.query.get_or_404(question_id)

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
        questions = Question.query.all()

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


@app.route('/admin/question/template')
def download_question_template():
    # Only admin can download template
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    # Define template columns
    cols = [
        'Question', 'Option A', 'Option B', 'Option C', 'Option D', 'Option E',
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

    subjects = Subject.query.all()

    if request.method == 'GET':
        return render_template('admin/generate_questions.html', subjects=subjects)

    # POST: handle generation
    try:
        subject_id = int(request.form.get('subject_id'))
        class_level = request.form.get('class_level', '').strip()
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

        user_prompt = (
            f"Subject: {subject.name}\nClass level: {class_level or 'unspecified'}\nTotal questions: {total_q}\n"
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

    exams = Exam.query.all()
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
                         total_subjects=Subject.query.count())

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['xlsx', 'xls']

@app.route('/admin/exams')
def admin_exams():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    
    exams = Exam.query.all()
    return render_template('admin/exams.html', exams=exams)


@app.route('/admin/exam/<int:exam_id>')
def admin_view_exam(exam_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    exam = Exam.query.get_or_404(exam_id)
    # Fetch questions for the exam subject
    try:
        subj_id = int(exam.subject_id)
    except Exception:
        subj_id = exam.subject_id

    questions = Question.query.filter_by(subject_id=subj_id).all()

    return render_template('admin/exam_detail.html', exam=exam, questions=questions)


@app.route('/admin/exam/<int:exam_id>/delete', methods=['POST'])
def admin_delete_exam(exam_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))

    exam = Exam.query.get_or_404(exam_id)

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

@app.route('/admin/exam/add', methods=['GET', 'POST'])
def add_exam():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    
    subjects = Subject.query.all()
    
    if request.method == 'POST':
        subject_id = int(request.form['subject_id'])
        title = request.form['title']
        description = request.form['description']
        duration = request.form['duration']
        
        # Calculate total marks for the exam based on questions in the subject
        questions = Question.query.filter_by(subject_id=subject_id).all()
        total_marks = sum(q.marks for q in questions)
        
        exam = Exam(
            subject_id=subject_id,
            title=title,
            description=description,
            duration=duration,
            code=generate_unique_exam_code(),
            total_marks=total_marks,
            created_by=session['user_id']
        )
        
        db.session.add(exam)
        db.session.commit()
        
        flash('Exam created successfully', 'success')
        return redirect(url_for('admin_exams'))
    
    return render_template('admin/add_exam.html', subjects=subjects)

@app.route('/admin/results')
def admin_results():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    
    exam_sessions = ExamSession.query.filter_by(status='completed').all()
    return render_template('admin/results.html', exam_sessions=exam_sessions)

# Student Routes
@app.route('/student/dashboard')
def student_dashboard():
    if 'user_id' not in session or session['role'] != 'student':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    
    exams = Exam.query.filter_by(is_active=True).all()
    completed_exams = ExamSession.query.filter_by(student_id=session['user_id'], status='completed').all()
    
    return render_template('student/dashboard.html', exams=exams, completed_exams=completed_exams)


@app.route('/start', methods=['GET'])
def start():
    # Public landing page where students enter their username/code and exam code
    return render_template('start.html')


@app.route('/start', methods=['POST'])
def start_exam():
    username_or_code = request.form.get('username_or_code', '').strip()
    exam_code = request.form.get('exam_code', '').strip()

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

    # Create an exam session and answer records (similar to take_exam)
    questions = Question.query.filter_by(subject_id=exam.subject_id).all()
    if not questions:
        flash('No questions available for this exam', 'danger')
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

@app.route('/student/exam/<int:exam_id>')
def take_exam(exam_id):
    if 'user_id' not in session or session['role'] != 'student':
        flash('Access denied', 'danger')
        return redirect(url_for('login'))
    
    exam = Exam.query.get_or_404(exam_id)
    
    # Check if student already has a COMPLETED or SUBMITTED session for this exam
    completed_session = ExamSession.query.filter_by(
        exam_id=exam_id, 
        student_id=session['user_id'],
        status='submitted'
    ).first()
    
    if completed_session:
        flash('You have already submitted this exam', 'info')
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
    # cannot view results without performing a normal login later.
    try:
        if session.get('temp_login') and session.get('temp_exam_session') == session_id:
            session.pop('user_id', None)
            session.pop('role', None)
            session.pop('temp_login', None)
            session.pop('temp_exam_session', None)
    except Exception:
        pass

    return {'status': 'success', 'score': total_score}

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
        wk = shutil.which('wkhtmltopdf')
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
                'margin-left': '0mm',
                'margin-right': '0mm',
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
    app.run(debug=True)