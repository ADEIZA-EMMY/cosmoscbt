import sqlite3

# Check test.db
try:
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM user WHERE role='student'")
    count = cursor.fetchone()[0]
    print(f"Students in test.db: {count}")
    conn.close()
except Exception as e:
    print(f"Error with test.db: {e}")

# Check cbt.db
try:
    conn = sqlite3.connect('cbt.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM user WHERE role='student'")
    count = cursor.fetchone()[0]
    print(f"Students in cbt.db: {count}")
    conn.close()
except Exception as e:
    print(f"Error with cbt.db: {e}")
