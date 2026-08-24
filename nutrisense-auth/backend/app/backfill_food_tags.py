"""
One-time backfill: tags every EXISTING food_items row with dietary flags
(is_vegetarian, is_vegan, contains_dairy, contains_gluten, contains_nuts).

Needed because you already imported USDA/SR Legacy/IFCT data before these
columns existed - new imports will get tagged automatically going forward,
but rows already in the database need this run once to catch up.

Run from the backend folder:
    python -m app.backfill_food_tags
"""
from app.database import SessionLocal
from app.models.food_item import FoodItem
from app.services.food_tags import classify_food


def backfill():
    db = SessionLocal()
    try:
        foods = db.query(FoodItem).all()
        print(f"Tagging {len(foods)} foods...")

        for food in foods:
            tags = classify_food(food.name)
            food.is_vegetarian = tags["is_vegetarian"]
            food.is_vegan = tags["is_vegan"]
            food.contains_dairy = tags["contains_dairy"]
            food.contains_gluten = tags["contains_gluten"]
            food.contains_nuts = tags["contains_nuts"]

        db.commit()
        print("Done.")

        vegan_count = db.query(FoodItem).filter(FoodItem.is_vegan == True).count()  # noqa: E712
        veg_count = db.query(FoodItem).filter(FoodItem.is_vegetarian == True).count()  # noqa: E712
        print(f"Tagged as vegetarian: {veg_count} / {len(foods)}")
        print(f"Tagged as vegan: {vegan_count} / {len(foods)}")
    finally:
        db.close()


if __name__ == "__main__":
    backfill()
