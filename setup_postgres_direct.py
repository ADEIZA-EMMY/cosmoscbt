#!/usr/bin/env python
"""
Simplified script to set up PostgreSQL database and user
No PgAdmin required - works directly with PostgreSQL command line
"""
import subprocess
import os
import sys

def run_psql_cmd(sql_cmd, user="postgres", password=None, host="localhost"):
    """Execute SQL command via psql"""
    env = os.environ.copy()
    if password:
        env['PGPASSWORD'] = password
    
    try:
        result = subprocess.run(
            ['psql', '-U', user, '-h', host, '-c', sql_cmd],
            capture_output=True,
            text=True,
            timeout=5,
            env=env
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def main():
    print("\n" + "="*70)
    print("  PostgreSQL Setup - Direct Database Configuration")
    print("="*70)
    
    # Hardcoded password for postgres superuser (you set this during PostgreSQL install)
    postgres_password = input("\nEnter your PostgreSQL 'postgres' superuser password: ").strip()
    
    if not postgres_password:
        print("  ✗ Password required!")
        return False
    
    print("\n[1] Testing PostgreSQL connection as postgres user...")
    code, out, err = run_psql_cmd("SELECT version();", user="postgres", password=postgres_password)
    
    if code != 0:
        print(f"  ✗ Connection failed: {err}")
        return False
    print("  ✓ Connected to PostgreSQL successfully")
    
    # Create database
    print("\n[2] Creating cbt_app database...")
    code, out, err = run_psql_cmd(
        "CREATE DATABASE cbt_app;",
        user="postgres",
        password=postgres_password
    )
    if code == 0:
        print("  ✓ Database cbt_app created")
    elif "already exists" in err.lower():
        print("  ⓘ Database cbt_app already exists")
    else:
        print(f"  ✗ Failed: {err}")
    
    # Create user
    print("\n[3] Creating cbt_user with password...")
    code, out, err = run_psql_cmd(
        "CREATE USER cbt_user WITH PASSWORD 'SecurePassword123!';",
        user="postgres",
        password=postgres_password
    )
    if code == 0:
        print("  ✓ User cbt_user created")
    elif "already exists" in err.lower():
        print("  ⓘ User cbt_user already exists - updating password...")
        code, out, err = run_psql_cmd(
            "ALTER USER cbt_user WITH PASSWORD 'SecurePassword123!';",
            user="postgres",
            password=postgres_password
        )
        if code == 0:
            print("  ✓ Password updated")
        else:
            print(f"  ✗ Failed: {err}")
    else:
        print(f"  ✗ Failed: {err}")
    
    # Grant privileges
    print("\n[4] Granting privileges...")
    commands = [
        "GRANT ALL PRIVILEGES ON DATABASE cbt_app TO cbt_user;",
        "ALTER ROLE cbt_user SET client_encoding TO 'utf8';",
        "ALTER ROLE cbt_user SET default_transaction_isolation TO 'read committed';",
    ]
    
    for cmd in commands:
        code, out, err = run_psql_cmd(cmd, user="postgres", password=postgres_password)
        if code != 0 and "already" not in err.lower():
            print(f"  ⚠ {cmd.split(';')[0]}: {err}")
    
    print("  ✓ Privileges granted")
    
    # Test new user connection
    print("\n[5] Testing cbt_user connection...")
    code, out, err = run_psql_cmd(
        "SELECT 'Connection successful!' as status;",
        user="cbt_user",
        password="SecurePassword123!"
    )
    
    if code == 0:
        print("  ✓ cbt_user can connect successfully!")
    else:
        print(f"  ✗ Connection test failed: {err}")
        return False
    
    print("\n" + "="*70)
    print("  ✓ PostgreSQL Setup Complete!")
    print("="*70)
    print("\nYour Flask app is configured to use:")
    print("  Host: localhost")
    print("  Port: 5432")
    print("  Database: cbt_app")
    print("  User: cbt_user")
    print("  Password: SecurePassword123!")
    print("\nNext step: Start your Flask app")
    print("\n")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
