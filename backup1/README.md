# NutriSense — Signup / Onboarding / Login / Food Diary

## Flow implemented (per requirements)
1. **Signup** — first name, last name, email, password + confirm (with live
   password-rule checklist and show/hide eye icon)
2. **Onboarding** — age, gender (Male=1 / Female=2), height, weight, activity
   level, dietary restrictions — saved to the database
3. **Redirect to Login** — after onboarding, the user is logged out and sent
   back to `/login` (per the required order: signup → info → login again)
4. **Login** — email + password, eye icon toggle
5. **Dashboard / Food diary** — search a real food dataset, log a meal with
   portion size, see today's logged entries, remove entries, sign out

## Folder structure
```
nutrisense-auth/
  backend/
    app/
      models/        User, HealthProfile, FoodItem, DiaryEntry
      routers/        auth, profile (onboarding), foods (search), diary (log/list/delete)
      data/seed_foods.json   starter food dataset (50 items)
      seed_foods.py   loads seed_foods.json into the database
  frontend/
    src/pages/        Signup, Login, Onboarding, Dashboard
```

## 1. Run the backend

```
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m app.seed_foods        # loads the starter food dataset (run once)
uvicorn app.main:app --reload --port 8000
```

This creates `nutrisense.db` with 4 tables: `users`, `health_profiles`,
`food_items`, `diary_entries`. Test any endpoint directly at
http://localhost:8000/docs.

## 2. Run the frontend (separate terminal)

```
cd frontend
npm install
npm run dev
```
Open http://localhost:5173

## About the food dataset

The task asked for foods to come from **USDA FoodData Central**
(https://fdc.nal.usda.gov) and **IFCT 2017** (https://ifct2017.github.io/),
using only the fields this project actually needs — not every column those
datasets provide.

**What's included right now:** `backend/app/data/seed_foods.json` — 50
real, commonly-used foods (Indian + Western) with only these fields:
`name, calories_kcal, protein_g, iron_mg, calcium_mg, vitamin_d_mcg,
vitamin_b12_mcg, folate_mcg, vitamin_a_mcg, vitamin_c_mg, magnesium_mg,
zinc_mg` — the exact same nutrient set your ML model was trained on, so a
diary entry's totals line up directly with the deficiency model.

**Important — this is a starter set, not the full dataset.** The full USDA
FoodData Central download is a multi-GB file, too large to fetch
automatically here. To load the real, full dataset:
1. Download the CSV from https://fdc.nal.usda.gov/download-datasets.html
2. Write a small script that reads it and, for each food, keeps ONLY the
   12 fields above (see the docstring at the top of `backend/app/seed_foods.py`
   for the exact mapping)
3. Insert those rows into `food_items` the same way `seed_foods.py` does

This keeps `food_items` lightweight instead of storing FoodData Central's
~300 raw columns per food, almost all of which this app never uses.

## Gender storage
Per the requirement, gender is stored as an integer in `health_profiles`:
`1 = Male`, `2 = Female` — not as a text string. The onboarding UI shows
"Male"/"Female" buttons, but sends `1`/`2` to the backend.
