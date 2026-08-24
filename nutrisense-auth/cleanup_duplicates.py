import sqlite3

DB_PATH = "backend/nutrisense_fresh.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Show records before cleanup
print("\nAssessment records BEFORE cleanup:\n")

cursor.execute("""
    SELECT id, user_id, overall_score, created_at
    FROM assessments
    ORDER BY user_id, created_at
""")

rows = cursor.fetchall()

for row in rows:
    print(row)

# Find duplicate assessments for the same user on the same date.
# Keep the newest record and delete older duplicates.

cursor.execute("""
    DELETE FROM assessments
    WHERE id NOT IN (
        SELECT MAX(id)
        FROM assessments
        GROUP BY
            user_id,
            DATE(created_at)
    )
""")

deleted = cursor.rowcount

conn.commit()

print(f"\nDeleted {deleted} duplicate assessment record(s).\n")

# Show records after cleanup
print("Assessment records AFTER cleanup:\n")

cursor.execute("""
    SELECT id, user_id, overall_score, created_at
    FROM assessments
    ORDER BY user_id, created_at
""")

rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()

print("\nCleanup complete!")