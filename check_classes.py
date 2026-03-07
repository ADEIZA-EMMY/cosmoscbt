import sqlite3

conn = sqlite3.connect('instance/cbt.db')
cursor = conn.cursor()

print("CHECKING STUDENT_CLASS TABLE:")
cursor.execute("SELECT COUNT(*) FROM student_class")
student_class_count = cursor.fetchone()[0]
print(f"StudentClass entries: {student_class_count}")

if student_class_count > 0:
    cursor.execute("SELECT id, name, school_id FROM student_class")
    for row in cursor.fetchall():
        print(f"  - id={row[0]}, name={row[1]}, school_id={row[2]}")

# Check inferred classes from students
print("\nINFERRED CLASSES (from students with student_class filled):")
cursor.execute("SELECT DISTINCT student_class FROM user WHERE role='student' AND student_class IS NOT NULL")
inferred_classes = cursor.fetchall()
if inferred_classes:
    for row in inferred_classes:
        print(f"  - {row[0]}")
else:
    print("  [NONE - all students have student_class=NULL]")

conn.close()
