"""
Loads app/data/seed_foods.json into the food_items table.
Run once after the backend is set up: python -m app.seed_foods

To use the REAL, full USDA FoodData Central dataset instead of this starter set:
1. Download the CSV from https://fdc.nal.usda.gov/download-datasets.html
2. Write a script that reads the CSV and, for each food, extracts ONLY these
   columns (matching this project's model features) and maps them into the
   same shape as seed_foods.json: name, calories_kcal, protein_g, iron_mg,
   calcium_mg, vitamin_d_mcg, vitamin_b12_mcg, folate_mcg, vitamin_a_mcg,
   vitamin_c_mg, magnesium_mg, zinc_mg
3. Insert those rows the same way this script does below.
This keeps the food_items table lightweight instead of storing FoodData
Central's full ~300 columns per food, most of which this app never uses.
"""
import json
from pathlib import Path

from app.database import SessionLocal, Base, engine
from app.models.food_item import FoodItem

Base.metadata.create_all(bind=engine)

SEED_PATH = Path(__file__).parent / "data" / "seed_foods.json"


def seed():
    db = SessionLocal()
    try:
        existing_count = db.query(FoodItem).count()
        if existing_count > 0:
            print(f"food_items already has {existing_count} rows — skipping seed. "
                  f"Delete nutrisense.db if you want to reseed from scratch.")
            return

        with open(SEED_PATH) as f:
            foods = json.load(f)

        for food in foods:
            db.add(FoodItem(**food))

        db.commit()
        print(f"Seeded {len(foods)} food items into food_items table.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
