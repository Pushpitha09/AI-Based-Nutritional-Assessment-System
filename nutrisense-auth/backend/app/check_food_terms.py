import sqlite3

conn = sqlite3.connect("nutrisense.db")

# Add/remove search terms here as needed
terms_to_check = [
    "sesame", "til", "gingelly", "curry leaf", "ponnaganni", "gogu",
    "amaranth", "ragi", "flaxseed", "flax", "agathi", "colocasia", "karivepaku","kadipatta","murraya"
]

for term in terms_to_check:
    rows = conn.execute(
        "SELECT name FROM food_items WHERE name LIKE ?", (f"%{term}%",)
    ).fetchall()
    print(f"\n'{term}' -> {len(rows)} match(es)")
    for r in rows[:5]:
        print("   ", r[0])

conn.close()
