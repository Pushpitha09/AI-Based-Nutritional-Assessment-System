"""
Imports the IFCT 2017 merged dataset into the food_items table.

BEFORE RUNNING THIS:
Copy ifct2017_merged.csv into: backend/app/data/ifct_raw/ifct2017_merged.csv

Column mapping below uses the REAL, confirmed column names from IFCT2017's
merged export (verified against the actual file - not guessed).

Note: IFCT does not include Vitamin B12 as a measured nutrient (expected -
B12 is rare in plant-based foods and Indian food composition tables
generally don't test for it). That field will be 0 for all IFCT-sourced
foods; USDA-sourced foods in the same table will still have real B12 values.

Run from the backend folder:
    python -m app.import_ifct
"""
import pandas as pd
from pathlib import Path

from app.database import SessionLocal, Base, engine
from app.models.food_item import FoodItem

Base.metadata.create_all(bind=engine)

RAW_PATH = Path(__file__).parent / "data" / "ifct_raw" / "ifct2017_merged.csv"

# our column -> exact IFCT2017 column name (confirmed from the real file's header)
COLUMN_MAP = {
    "name_col": "name",
    "calories_kcal": "enerc",
    "protein_g": "protcnt",
    "iron_mg": "fe",
    "calcium_mg": "ca",
    "vitamin_d_mcg": "vitd",
    "vitamin_b12_mcg": None,       # not present in IFCT - stays 0
    "folate_mcg": "folsum",
    "vitamin_a_mcg": "vita",
    "vitamin_c_mg": "vitc",
    "magnesium_mg": "mg",
    "zinc_mg": "zn",
}


def import_ifct():
    if not RAW_PATH.exists():
        print(f"ERROR: file not found at {RAW_PATH}")
        print("Copy ifct2017_merged.csv into backend/app/data/ifct_raw/ first.")
        return

    print(f"Loading {RAW_PATH.name}...")
    df = pd.read_csv(RAW_PATH)
    print(f"Found {len(df)} foods, {len(df.columns)} columns.\n")

    print("Checking that every mapped column actually exists in this file...")
    missing = []
    for our_col, real_col in COLUMN_MAP.items():
        if real_col is None:
            print(f"  {our_col:20s} -> (not in IFCT, will be 0)")
            continue
        if real_col not in df.columns:
            print(f"  {our_col:20s} -> '{real_col}' NOT FOUND IN FILE")
            missing.append(our_col)
        else:
            print(f"  {our_col:20s} -> '{real_col}' OK")

    if missing:
        print(f"\nERROR: {len(missing)} expected column(s) missing from your file: {missing}")
        print("This shouldn't happen if you're using the same ifct2017_merged.csv - stopping.")
        return

    db = SessionLocal()
    try:
        already_imported = db.query(FoodItem).filter(FoodItem.source == "ifct").count()
        if already_imported > 0:
            print(f"\n{already_imported} IFCT foods are already in the database - skipping import "
                  f"to avoid duplicates.")
            print("If you want to reimport (e.g. after fixing a column mapping), delete the old")
            print("IFCT rows first:")
            print('  python -c "import sqlite3; conn = sqlite3.connect(\'nutrisense.db\'); '
                  'conn.execute(\\"DELETE FROM food_items WHERE source=\'ifct\'\\"); conn.commit()"')
            return

        print(f"\nInserting {len(df)} foods into the database...")
        inserted = 0
        for _, row in df.iterrows():
            def get_val(col_key):
                real_col = COLUMN_MAP[col_key]
                if real_col is None:
                    return 0.0
                val = row[real_col]
                return float(val) if pd.notna(val) else 0.0

            name = row[COLUMN_MAP["name_col"]]
            if pd.isna(name):
                continue

            db.add(FoodItem(
                name=str(name),
                source="ifct",
                calories_kcal=get_val("calories_kcal"),
                protein_g=get_val("protein_g"),
                iron_mg=get_val("iron_mg"),
                calcium_mg=get_val("calcium_mg"),
                vitamin_d_mcg=get_val("vitamin_d_mcg"),
                vitamin_b12_mcg=get_val("vitamin_b12_mcg"),
                folate_mcg=get_val("folate_mcg"),
                vitamin_a_mcg=get_val("vitamin_a_mcg"),
                vitamin_c_mg=get_val("vitamin_c_mg"),
                magnesium_mg=get_val("magnesium_mg"),
                zinc_mg=get_val("zinc_mg"),
            ))
            inserted += 1

        db.commit()
        print(f"Done. {inserted} IFCT foods added to food_items.")
    finally:
        db.close()


if __name__ == "__main__":
    import_ifct()
