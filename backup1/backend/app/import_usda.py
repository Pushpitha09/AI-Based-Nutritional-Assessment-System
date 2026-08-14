"""
Imports real USDA FoodData Central data into the food_items table.

BEFORE RUNNING THIS:
1. Download "Foundation Foods" (CSV) from https://fdc.nal.usda.gov/download-datasets.html
2. Unzip it so these 3 files sit inside: backend/app/data/usda_raw/
     - food.csv
     - nutrient.csv
     - food_nutrient.csv

WHY 3 FILES: USDA doesn't give one flat file with a "calories" column etc.
- food.csv          -> just food names (fdc_id -> description)
- nutrient.csv       -> a lookup of nutrient IDs to names (id -> "Protein", "Iron, Fe", ...)
- food_nutrient.csv  -> the actual values, one row per (food, nutrient) pair
This script joins all three together so each food becomes ONE row with just
the 12 fields this project actually uses.

Run from the backend folder:
    python -m app.import_usda
"""
import pandas as pd
from pathlib import Path

from app.database import SessionLocal, Base, engine
from app.models.food_item import FoodItem

Base.metadata.create_all(bind=engine)

RAW_DIR = Path(__file__).parent / "data" / "usda_raw"

# Maps: our column name -> what to search for in nutrient.csv's "name" column
# (USDA's exact wording varies slightly between dataset releases, so we match
# on a distinctive substring rather than an exact string.)
NUTRIENT_NAME_MAP = {
    "calories_kcal": "Energy",
    "protein_g": "Protein",
    "iron_mg": "Iron, Fe",
    "calcium_mg": "Calcium, Ca",
    "vitamin_d_mcg": "Vitamin D (D2 + D3)",
    "vitamin_b12_mcg": "Vitamin B-12",
    "folate_mcg": "Folate, total",
    "vitamin_a_mcg": "Vitamin A, RAE",
    "vitamin_c_mg": "Vitamin C",
    "magnesium_mg": "Magnesium, Mg",
    "zinc_mg": "Zinc, Zn",
}


def find_nutrient_ids(nutrient_df: pd.DataFrame) -> dict:
    """For each of our 11 nutrients, find the matching USDA nutrient_id."""
    resolved = {}
    for our_col, search_text in NUTRIENT_NAME_MAP.items():
        match = nutrient_df[nutrient_df["name"].str.contains(search_text, case=False, na=False)]
        if our_col == "calories_kcal":
            # "Energy" appears twice (kcal and kJ) - keep only the kcal one
            match = match[match["unit_name"].str.upper() == "KCAL"]
        if match.empty:
            print(f"  WARNING: no match found for '{search_text}' (column: {our_col}) - it will be 0 for all foods")
            resolved[our_col] = None
        else:
            resolved[our_col] = match.iloc[0]["id"]
            print(f"  matched '{search_text}' -> nutrient_id {resolved[our_col]}")
    return resolved


def import_usda():
    print("Loading CSV files...")
    food_df = pd.read_csv(RAW_DIR / "food.csv", usecols=["fdc_id", "description"])
    nutrient_df = pd.read_csv(RAW_DIR / "nutrient.csv", usecols=["id", "name", "unit_name"])
    food_nutrient_df = pd.read_csv(
        RAW_DIR / "food_nutrient.csv", usecols=["fdc_id", "nutrient_id", "amount"]
    )

    print("\nMatching nutrient names to USDA nutrient IDs...")
    nutrient_ids = find_nutrient_ids(nutrient_df)

    print("\nPivoting food_nutrient.csv so each food becomes one row...")
    # Keep only rows for the 11 nutrients we care about
    wanted_ids = [v for v in nutrient_ids.values() if v is not None]
    filtered = food_nutrient_df[food_nutrient_df["nutrient_id"].isin(wanted_ids)]

    # Pivot: rows = fdc_id, columns = nutrient_id, values = amount
    pivoted = filtered.pivot_table(index="fdc_id", columns="nutrient_id", values="amount", aggfunc="first")

    # Rename pivoted columns from nutrient_id back to our column names
    id_to_col = {v: k for k, v in nutrient_ids.items() if v is not None}
    pivoted = pivoted.rename(columns=id_to_col)

    print("Joining with food names...")
    merged = food_df.merge(pivoted, on="fdc_id", how="inner")

    # Fill any missing nutrient values with 0 rather than leaving them blank
    for col in NUTRIENT_NAME_MAP:
        if col not in merged.columns:
            merged[col] = 0.0
        merged[col] = merged[col].fillna(0.0)

    # USDA Foundation Foods has many lab-sample duplicates of the same food name,
    # some of which never had calories measured (incomplete data, not real 0-kcal
    # foods). Drop those - they're not useful for this app and just clutter search.
    before = len(merged)
    merged = merged[merged["calories_kcal"] > 0]
    print(f"Dropped {before - len(merged)} entries with no measured calories (incomplete samples).")

    print(f"\nInserting {len(merged)} foods into the database...")
    db = SessionLocal()
    try:
        for _, row in merged.iterrows():
            db.add(FoodItem(
                name=row["description"],
                source="usda",
                calories_kcal=row["calories_kcal"],
                protein_g=row["protein_g"],
                iron_mg=row["iron_mg"],
                calcium_mg=row["calcium_mg"],
                vitamin_d_mcg=row["vitamin_d_mcg"],
                vitamin_b12_mcg=row["vitamin_b12_mcg"],
                folate_mcg=row["folate_mcg"],
                vitamin_a_mcg=row["vitamin_a_mcg"],
                vitamin_c_mg=row["vitamin_c_mg"],
                magnesium_mg=row["magnesium_mg"],
                zinc_mg=row["zinc_mg"],
            ))
        db.commit()
        print(f"Done. {len(merged)} real USDA foods added to food_items.")
    finally:
        db.close()


if __name__ == "__main__":
    import_usda()
