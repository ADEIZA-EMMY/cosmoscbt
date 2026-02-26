-- PostgreSQL setup script for CBT application
-- Run this as the postgres superuser: psql -U postgres -f setup_postgres.sql

-- Step 1: Create database
CREATE DATABASE cbt_app;

-- Step 2: Create user with password
CREATE USER cbt_user WITH PASSWORD 'Adeizaemma47';

-- Step 3: Configure user settings
ALTER ROLE cbt_user SET client_encoding TO 'utf8';
ALTER ROLE cbt_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE cbt_user SET default_transaction_deferrable TO on;
ALTER ROLE cbt_user SET default_timezone TO 'UTC';

-- Step 4: Grant database privileges
GRANT ALL PRIVILEGES ON DATABASE cbt_app TO cbt_user;

-- Step 5: Connect to database and grant schema permissions
\c cbt_app

GRANT ALL ON SCHEMA public TO cbt_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cbt_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO cbt_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO cbt_user;

-- Verify setup
SELECT 'Database setup complete!' as status;
