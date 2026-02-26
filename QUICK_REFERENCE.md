# PostgreSQL Quick Reference Guide - CBT Application

**Last Updated:** February 24, 2026  
**Status:** ✓ Complete

---

## ⚡ Quick Start (5 Minutes)

### 1. **Create PostgreSQL Database**
```bash
# Open PostgreSQL command line
psql -U postgres

# Execute these commands:
CREATE DATABASE cbt_app;
CREATE USER cbt_user WITH PASSWORD 'SecurePassword123!';
GRANT ALL PRIVILEGES ON DATABASE cbt_app TO cbt_user;
\q
```

### 2. **Create .env File**
```bash
# Create .env in project root
DATABASE_URL=postgresql://cbt_user:SecurePassword123!@localhost:5432/cbt_app
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here
```

### 3. **Initialize Database**
```bash
python init_postgres.py
```

### 4. **Run Application**
```bash
python code1.py
```

### 5. **Access Application**
- Open: http://localhost:5000
- Login: admin / admin123
- SuperAdmin: /6869

---

## 📋 Configuration Checklist

### Database Setup
- [ ] PostgreSQL installed (`psql --version`)
- [ ] psycopg2 installed (`pip list | grep psycopg`)
- [ ] Database created: `cbt_app`
- [ ] User created: `cbt_user` with password
- [ ] Privileges granted to user
- [ ] Connection tested: `psql -U cbt_user -d cbt_app`

### Application Configuration
- [ ] `.env` file created
- [ ] `DATABASE_URL` set correctly
- [ ] `python-dotenv` installed
- [ ] `init_postgres.py` ran successfully
- [ ] Tables created (verify with tests)
- [ ] Application starts without errors

### Verification
- [ ] Public routes working (/login, /register, /start)
- [ ] Admin routes accessible (/admin/dashboard, etc.)
- [ ] Database queries working (test users, exams)
- [ ] File uploads working
- [ ] All CRUD operations functional

---

## 🔧 Common Configuration Scenarios

### Scenario 1: Docker PostgreSQL
```bash
docker run --name cbt_postgres \
  -e POSTGRES_PASSWORD=SecurePassword123! \
  -d -p 5432:5432 postgres:15

# Update DATABASE_URL
DATABASE_URL=postgresql://postgres:SecurePassword123!@localhost:5432/postgres
```

### Scenario 2: Cloud Database (AWS RDS)
```bash
# Create RDS instance first, then:
DATABASE_URL=postgresql://admin:password@your-instance.rdsxxxxx.us-east-1.amazonaws.com:5432/cbt_app
```

### Scenario 3: Heroku Deployment
```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:hobby-dev
heroku config:set FLASK_ENV=production
git push heroku main
heroku run python init_postgres.py
```

### Scenario 4: Local Development (Windows)
```bash
# PowerShell - Start PostgreSQL service
Start-Service -Name PostgreSQL15

# Set DATABASE_URL
$env:DATABASE_URL="postgresql://cbt_user:pass@localhost:5432/cbt_app"

# Run
python code1.py
```

---

## 🧪 Testing Routes

### Test Commands
```bash
# Test all routes
python test_postgres_routes.py

# Test database connection only
python test_db_connection.py

# Run quick server test
python -c "from code1 import app; app.run(debug=True)"
```

### Manual Test Cases

#### 1. Authentication Flow
```
GET /login → Register page displays
POST /register → New student created
POST /login → Login successful → Redirect to /student/dashboard
GET /admin/dashboard → Admin access granted (with admin account)
```

#### 2. Question Management
```
GET /admin/questions → Questions list displays
GET /admin/question/template → Download CSV template
POST /admin/question/upload → Upload Excel file
GET /admin/question/generate → OpenAI generation form
POST /admin/question/generate/commit → Save generated questions
```

#### 3. Exam Flow
```
GET /admin/exams → Exam list displays
POST /admin/exam/add → Create new exam
GET /start → Student exam startup
POST /start → Start exam session
GET /start/exam/<id> → Take exam
POST (submit answers) → Save responses
GET /student/result/<id>/pdf → Download results
```

#### 4. File Operations
```
POST /admin/students/import_xlsx → Import student list
POST /admin/question/upload → Upload questions
POST /student/upload_passport → Upload passport photo
GET /admin/results/export_subject → Export results
```

---

## 🔐 Connection Strings

| Environment | Format |
|-------------|--------|
| **Local Dev** | `postgresql://cbt_user:pwd@localhost:5432/cbt_app` |
| **Docker** | `postgresql://postgres:pwd@db:5432/cbt_app` |
| **Heroku** | `postgresql://user:pwd@host.compute.amazonaws.com:5432/db` |
| **AWS RDS** | `postgresql://admin:pwd@rds-instance.us-east-1.rds.amazonaws.com:5432/cbt_app` |
| **Google Cloud** | `postgresql://user:pwd@/db?unix_socket_dir=/cloudsql/project:region:instance` |

---

## 🚀 Active Route Categories (Complete List)

| Category | Count | Routes |
|----------|-------|--------|
| **Authentication** | 4 | login, register, logout, superadmin |
| **Admin Dashboard** | 8 | dashboard, schools, classes, subjects |
| **Questions** | 15 | add, upload, generate, delete, template |
| **Students** | 12 | manage, import, export, edit, delete |
| **Exams** | 12 | create, edit, manage codes, access |
| **Results** | 5 | view, export, print, download PDF |
| **File I/O** | 10 | upload, download, serve media |
| **Community** | 4 | posts, moderate, like, comments |
| **System** | 15 | diagnostics, settings, logs |
| **API/JSON** | 3 | students data, exam data |
| **TOTAL** | **100+** | All routes operational ✓ |

---

## ⚠️ Troubleshooting Quick Fixes

| Error | Solution |
|-------|----------|
| **Connection refused** | `brew services start postgresql` (macOS) or check Windows Services |
| **Role does not exist** | Create user: `CREATE USER cbt_user WITH PASSWORD '...'` |
| **Database does not exist** | Create: `CREATE DATABASE cbt_app;` |
| **psycopg2 not found** | `pip install psycopg2-binary>=2.9.7` |
| **No such table** | Run: `python init_postgres.py` |
| **Bad connection string** | Check `.env` file and verify credentials |
| **Permission denied** | Grant privileges: `GRANT ALL ON DATABASE cbt_app TO cbt_user;` |

---

## 📊 Database Statistics

**After initialization, your database contains:**
- Users table (ready for students/admins)
- Schools table (multi-tenant support)
- Subjects table (Nigerian curriculum or custom)
- Exams table (with unique codes)
- Questions table (with image support)
- Exam Sessions table (tracks student attempts)
- Answers table (stores responses)
- Various admin tables (notes, appointments, feedback)

**Estimated Storage:**
- Empty DB: ~1-2 MB
- With 1000 questions: ~5-10 MB
- With 10k+ student records: ~50-100 MB

---

## 🖥️ System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **PostgreSQL** | 11+ | 14+ |
| **Python** | 3.8 | 3.11+ |
| **RAM** | 512 MB | 2+ GB |
| **Disk** | 100 MB | 500+ MB |
| **CPU** | Dual-core | Quad-core |

---

## 📱 Port Information

| Service | Port | Purpose |
|---------|------|---------|
| **Flask App** | 5000 | Web application |
| **PostgreSQL** | 5432 | Database |
| **pgAdmin (optional)** | 5050 | Database GUI |
| **Redis (optional)** | 6379 | Caching |

---

## 🔄 Database Maintenance

### Backup Database
```bash
# Windows
"C:\Program Files\PostgreSQL\15\bin\pg_dump.exe" -U cbt_user -d cbt_app > backup.sql

# macOS/Linux
pg_dump -U cbt_user -d cbt_app > backup.sql
```

### Restore Database
```bash
psql -U cbt_user -d cbt_app < backup.sql
```

### Reset Database (Development Only!)
```bash
# Delete all data and reinitialize
python -c "from code1 import app, db; app.app_context().push(); db.drop_all(); db.create_all(); print('Reset complete')"
```

### View Database Size
```sql
SELECT 
  datname,
  pg_size_pretty(pg_database_size(datname)) AS size
FROM pg_database
WHERE datname = 'cbt_app';
```

---

## 📚 Key Files Created

| File | Purpose |
|------|---------|
| `.env` | Environment configuration |
| `init_postgres.py` | Database initialization |
| `test_postgres_routes.py` | Comprehensive route testing |
| `test_db_connection.py` | Connection troubleshooting |
| `POSTGRESQL_SETUP_GUIDE.md` | Complete documentation |

---

## ✅ Verification Commands

```bash
# Check PostgreSQL version
psql --version

# Check Python packages
pip list | grep -E "Flask|SQLAlchemy|psycopg2"

# Test database connection
python test_db_connection.py

# Test all routes
python test_postgres_routes.py

# Run application
python code1.py
```

---

## 📞 Support Resources

- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **Flask-SQLAlchemy**: https://flask-sqlalchemy.palletsprojects.com/
- **psycopg2 Docs**: https://www.psycopg.org/
- **SQLAlchemy**: https://docs.sqlalchemy.org/

---

## 🎯 Success Criteria

✓ PostgreSQL running  
✓ Database created  
✓ All tables initialized  
✓ 100+ routes active  
✓ Authentication working  
✓ File uploads functional  
✓ Student registration working  
✓ Exam creation and taking functional  
✓ Results and PDF download working  
✓ Admin dashboard accessible

**When ALL criteria are met, your system is ready for production!** 🚀

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-24 | Initial setup guide |
| - | - | Comprehensive route documentation |
| - | - | Test scripts included |
| - | - | Configuration helper created |

---

**Next Steps:**
1. Read POSTGRESQL_SETUP_GUIDE.md for detailed instructions
2. Run `python configure_postgres.py` for interactive setup
3. Run `python test_postgres_routes.py` to verify everything works
4. Start with `python code1.py`

**Questions?** Check the detailed guide or troubleshooting section above.

