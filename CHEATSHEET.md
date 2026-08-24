# NutriSense — Command Cheat Sheet

## FIRST-TIME SETUP (only needed once, or after a fresh clone)

### Backend setup
```powershell
cd nutrisense-auth\backend
python3 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend setup
```powershell
cd nutrisense-auth\frontend
npm install
```

---

## EVERY TIME YOU OPEN A NEW TERMINAL

Always activate the venv first, in every new backend terminal:
```powershell
cd nutrisense-auth\backend
venv\Scripts\activate
```
(You'll know it worked if your prompt shows `(venv)` at the start.)

---

## STARTING THE APP (two terminals, running at the same time)

**Terminal 1 — backend:**
```powershell
cd nutrisense-auth\backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — frontend:**
```powershell
cd nutrisense-auth\frontend
npm run dev
```

Then open: **http://localhost:5173**

API docs / manual testing: **http://localhost:8000/docs**

---

## IMPORTING FOOD DATASETS (run once per fresh database)

All of these run from the `backend` folder with venv activated.

**Starter set (50 foods, quick, no download needed):**
```powershell
python -m app.seed_foods
```

**USDA Foundation Foods** (needs `food.csv`, `nutrient.csv`, `food_nutrient.csv` in `app\data\usda_raw\`):
```powershell
python -m app.import_usda
```

**USDA SR Legacy** (needs the same 3 files, but in `app\data\usda_sr_legacy_raw\`):
```powershell
python -m app.import_usda_sr_legacy
```

**IFCT 2017** (needs `ifct2017_merged.csv` in `app\data\ifct_raw\`):
```powershell
python -m app.import_ifct
```

All of these are safe to run more than once — they auto-skip if that source's data is already loaded, so you won't get duplicates.

---

## MODEL ARTIFACTS (needed for the Assessment feature to work)

Download from Google Drive and place these 3 files here:
```
nutrisense-auth\backend\app\ml_artifacts\deficiency_model.joblib
nutrisense-auth\backend\app\ml_artifacts\preprocess.joblib
nutrisense-auth\backend\app\ml_artifacts\meta.json
```
Without these, `/assess` will return a 500 error saying they're missing.

---

## RESETTING THE DATABASE (wipes everything — users, diary, food, all of it)

1. Stop the backend server first (Ctrl+C in that terminal) — you can't delete the file while the server has it open
2. ```powershell
   del nutrisense.db
   ```
3. Re-run whichever import commands you need from the section above
4. Restart the server

---

## QUICK DATABASE CHECKS

**How many foods, by source:**
```powershell
python -c "import sqlite3; print(sqlite3.connect('nutrisense.db').execute('SELECT source, COUNT(*) FROM food_items GROUP BY source').fetchall())"
```

**Total food count:**
```powershell
python -c "import sqlite3; print(sqlite3.connect('nutrisense.db').execute('SELECT COUNT(*) FROM food_items').fetchone())"
```

---

## THE FULL APP FLOW (to test everything works)

1. Sign up (first name, last name, email, password)
2. Fill in health profile (onboarding) — you'll be logged out after saving
3. Log back in
4. Food diary — search a food, log a portion, repeat for **7 different dates** (Assessment requires 7 distinct days minimum)
5. (Optional) Lab results — enter blood test values
6. Assessment — click "Run assessment"

---

## GIT — pushing your work

```powershell
cd nutrisense-auth
git add .
git commit -m "describe what changed here"
git push
```
If it asks for login, use a GitHub Personal Access Token, not your password.

---

## COMMON ERRORS, QUICK FIXES

| Error | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'X'` | venv not activated — run `venv\Scripts\activate` |
| `&&` PowerShell syntax error | Run each command on its own line, don't chain with `&&` |
| `NameError: name 'df' is not defined` (Colab) | Session disconnected — re-run your mount/reload cells from the top |
| `del nutrisense.db` fails, file in use | Stop the running server first (Ctrl+C), then delete |
| Port 8000 or 5173 already in use | Close the old terminal running that server, or restart VS Code |
