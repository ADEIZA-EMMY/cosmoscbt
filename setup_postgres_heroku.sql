-- Heroku-safe subset of setup_postgres.sql
-- Removed: CREATE DATABASE, CREATE USER, ALTER ROLE, \connect, and GRANTs to specific roles
-- Run privileged commands (database/role creation) on a superuser-managed Postgres instance.

-- If you have schema/table creation statements, place them below.
-- (Original script contained only database/role creation and grants; nothing schema-specific to run on Heroku.)

-- -------------------------
-- Schema / Tables (Heroku-safe)
-- -------------------------

CREATE TABLE IF NOT EXISTS users (
	id SERIAL PRIMARY KEY,
	username TEXT UNIQUE NOT NULL,
	email TEXT UNIQUE,
	hashed_password TEXT,
	is_admin BOOLEAN DEFAULT FALSE,
	created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS exams (
	id SERIAL PRIMARY KEY,
	title TEXT NOT NULL,
	description TEXT,
	duration_minutes INTEGER,
	created_by INTEGER,
	created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS questions (
	id SERIAL PRIMARY KEY,
	exam_id INTEGER NOT NULL,
	question_text TEXT NOT NULL,
	question_type TEXT DEFAULT 'mcq',
	points INTEGER DEFAULT 1,
	FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS options (
	id SERIAL PRIMARY KEY,
	question_id INTEGER NOT NULL,
	option_text TEXT NOT NULL,
	is_correct BOOLEAN DEFAULT FALSE,
	FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS results (
	id SERIAL PRIMARY KEY,
	user_id INTEGER NOT NULL,
	exam_id INTEGER NOT NULL,
	score NUMERIC,
	started_at TIMESTAMPTZ,
	finished_at TIMESTAMPTZ,
	FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
	FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_questions_exam_id ON questions(exam_id);
CREATE INDEX IF NOT EXISTS idx_options_question_id ON options(question_id);
CREATE INDEX IF NOT EXISTS idx_results_user_exam ON results(user_id, exam_id);

SELECT 'Heroku-safe script created with schema DDL' AS status;
