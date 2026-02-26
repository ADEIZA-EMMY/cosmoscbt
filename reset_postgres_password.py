#!/usr/bin/env python
"""
Reset PostgreSQL postgres user password on Windows
"""
import subprocess
import os
import time
import sys

def run_command(cmd, shell=True):
    """Run a command and return output"""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def main():
    print("\n" + "="*70)
    print("  PostgreSQL Password Reset Utility (Windows)")
    print("="*70)
    
    # Test current connection
    print("\n[1] Testing current PostgreSQL connection...")
    code, out, err = run_command('psql --version')
    if code != 0:
        print("  ✗ PostgreSQL not found in PATH")
        print("  Please ensure PostgreSQL is installed")
        return False
    print("  ✓ PostgreSQL found")
    
    # Try to connect as postgres with common passwords
    print("\n[2] Attempting connection with common passwords...")
    common_passwords = ['postgres', 'password', 'admin', '123456', 'postgres123']
    correct_password = None
    
    for pwd in common_passwords:
        print(f"  Trying password: {pwd[:4]}{'*' * (len(pwd)-4)}...", end=" ")
        code, out, err = run_command(f'psql -U postgres -h localhost -c "SELECT 1;" 2>&1', shell=True)
        # Set the password via environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = pwd
        try:
            result = subprocess.run(
                ['psql', '-U', 'postgres', '-h', 'localhost', '-c', 'SELECT 1;'],
                capture_output=True,
                text=True,
                timeout=3,
                env=env
            )
            if result.returncode == 0:
                print("✓ SUCCESS!")
                correct_password = pwd
                break
            else:
                print("✗")
        except Exception as e:
            print("✗")
    
    if not correct_password:
        print("\n  ✗ Could not connect with common passwords")
        print("\n  Please do one of the following:")
        print("  1. If you have pgAdmin installed, use it to reset the password")
        print("  2. Try the manual process in reset_postgres_password.ps1")
        print("  3. Reinstall PostgreSQL with a known password")
        return False
    
    print(f"\n  ✓ Connected successfully with existing password!")
    
    # Now reset it to a new password
    print("\n[3] Resetting postgres password...")
    new_password = 'postgres123'
    
    env = os.environ.copy()
    env['PGPASSWORD'] = correct_password
    
    try:
        sql_cmd = f"ALTER USER postgres WITH PASSWORD '{new_password}';"
        result = subprocess.run(
            ['psql', '-U', 'postgres', '-h', 'localhost', '-c', sql_cmd],
            capture_output=True,
            text=True,
            timeout=5,
            env=env
        )
        if result.returncode == 0:
            print(f"  ✓ Password reset to: {new_password}")
        else:
            print(f"  ✗ Failed to reset password")
            print(f"  Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False
    
    # Test new password
    print("\n[4] Testing new password...")
    env = os.environ.copy()
    env['PGPASSWORD'] = new_password
    
    try:
        result = subprocess.run(
            ['psql', '-U', 'postgres', '-h', 'localhost', '-c', 'SELECT version();'],
            capture_output=True,
            text=True,
            timeout=5,
            env=env
        )
        if result.returncode == 0:
            print("  ✓ New password works!")
        else:
            print(f"  ✗ New password failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False
    
    print("\n" + "="*70)
    print("  ✓ Password Reset Complete!")
    print("="*70)
    print(f"\nPostgreSQL postgres user password: {new_password}")
    print("\nNext steps:")
    print("1. Run: python setup_cbt_postgres.py")
    print("2. Or run: psql -U postgres -h localhost -f setup_postgres.sql")
    print("\n")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
