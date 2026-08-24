import sqlite3

conn = sqlite3.connect("nutrisense.db")
deleted = conn.execute("DELETE FROM food_items WHERE source = 'ifct'").rowcount
conn.commit()
conn.close()
print(f"Deleted {deleted} IFCT rows.")
