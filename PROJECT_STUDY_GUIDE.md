# NutriSense Project Study and Review Guide

This guide explains the complete NutriSense application as it exists in this repository. It is written for project demonstrations, viva questions, code reviews, and maintenance.

The project is an educational nutrition application that:

1. Authenticates users.
2. Collects a health profile, dietary preferences, food diary entries, and optional laboratory values.
3. Aggregates dietary intake over multiple days.
4. Uses a trained machine-learning model to estimate deficiency risk for ten nutrients.
5. Shows rule-based recommended foods for high-risk nutrients.
6. Generates a rule-based seven-day meal plan.
7. Shows progress across historical assessments.

This is an educational or internship demonstration. It is not a medical device, a diagnostic system, or clinical advice.

## 1. One-minute project explanation

NutriSense is a full-stack web application. The React frontend collects user information and displays results. The FastAPI backend authenticates requests, stores data in SQLite through SQLAlchemy, performs nutrient aggregation, loads a pre-trained Random Forest model, and returns assessment results. Food recommendations are deliberately separate from machine learning: the model estimates risk, while a deterministic database lookup selects foods containing the relevant nutrient and applies dietary filters.

The most important design separation is:

```text
User diary + profile
        |
        v
Daily nutrient averages
        |
        v
Random Forest -> deficiency probabilities
        |
        +------------------------------+
        |                              |
        v                              v
Assessment risks              Rule-based food recommendations
        |                              |
        +--------------+---------------+
                       v
              Rule-based meal plan
```

The Random Forest does not recommend foods. It only estimates the probability of deficiency for each supported nutrient.

## 2. Technology stack

### Frontend

- React 19: component-based user interface.
- Vite: frontend development server and production bundler.
- React Router: client-side page routing.
- `lucide-react`: icons used in the interface.
- Recharts: charts used by dashboard/progress views.
- JavaScript and JSX: application implementation.

Main configuration: [frontend/package.json](nutrisense-auth/frontend/package.json) and [vite.config.js](nutrisense-auth/frontend/vite.config.js).

### Backend

- Python: backend language.
- FastAPI: REST API framework, validation integration, dependency injection, and automatic OpenAPI documentation.
- Uvicorn: ASGI server used to run FastAPI.
- SQLAlchemy: ORM used to define models and query SQLite.
- SQLite: local relational database.
- Pydantic: request and response schemas.
- Passlib with bcrypt: password hashing.
- `python-jose`: JWT creation and validation.
- pandas: tabular feature preparation and data processing.
- scikit-learn: Random Forest model and preprocessing support.
- LightGBM, XGBoost, and CatBoost: model comparison during training; they are dependencies because the notebooks compare these models.
- joblib: loading serialized model and preprocessing artifacts.

Backend dependencies are listed in [requirements.txt](nutrisense-auth/backend/requirements.txt).

### Data sources

The project uses a normalized internal `food_items` table rather than querying external food APIs at runtime. Food rows can be loaded from:

- A small local seed set.
- IFCT 2017, the Indian Food Composition Tables dataset.
- USDA FoodData Central Foundation Foods.
- USDA SR Legacy data.

Import code is in [import_ifct.py](nutrisense-auth/backend/app/import_ifct.py), [import_usda.py](nutrisense-auth/backend/app/import_usda.py), [import_usda_sr_legacy.py](nutrisense-auth/backend/app/import_usda_sr_legacy.py), and [seed_foods.py](nutrisense-auth/backend/app/seed_foods.py).

## 3. Repository map

```text
repository root
|-- README.md                         Short project description
|-- CHEATSHEET.md                     Setup, run, import, and troubleshooting commands
|-- PROJECT_STUDY_GUIDE.md            This detailed review guide
|-- *.ipynb                           Milestone notebooks for data and model work
|-- Models/models/                    Copied or earlier model artifacts
|-- datadata/                         Dataset download/import helpers
|-- sense.db                           Existing database file in the workspace
`-- nutrisense-auth/
    |-- backend/
    |   |-- requirements.txt
    |   `-- app/
    |       |-- main.py               FastAPI application entrypoint
    |       |-- database.py            SQLite engine and session dependency
    |       |-- auth.py                Password hashing and JWT functions
    |       |-- schemas.py              Pydantic API contracts
    |       |-- models/                SQLAlchemy database models
    |       |-- routers/               HTTP endpoint modules
    |       |-- services/              Assessment, recommendations, tags, meal plans
    |       |-- data/                  Seed and raw food data
    |       `-- ml_artifacts/           Runtime model, preprocessing, metadata, metrics
    `-- frontend/
        |-- package.json
        |-- vite.config.js
        `-- src/
            |-- App.jsx               Routes
            |-- api.js                Frontend-to-backend requests
            |-- AuthContext.jsx       Login state and local storage
            |-- index.css              Shared styling
            `-- pages/                 Screens and protected route components
```

The active web application is under `nutrisense-auth`. The notebooks and root data helpers are mainly for experimentation, preparation, and model development rather than runtime request handling.

## 4. How to run the project

### Backend setup

From the repository root:

```powershell
cd nutrisense-auth\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The backend is available at `http://localhost:8000`.

FastAPI's interactive documentation is available at `http://localhost:8000/docs`.

### Frontend setup

In a second terminal:

```powershell
cd nutrisense-auth\frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

The frontend API base URL is currently hard-coded as `http://localhost:8000` in [api.js](nutrisense-auth/frontend/src/api.js). The Vite configuration does not proxy API requests; the browser calls the backend directly.

### Database behavior

[database.py](nutrisense-auth/backend/app/database.py) uses this environment variable:

```text
NUTRISENSE_DATABASE_FILE
```

If it is not set, the backend uses `nutrisense_fresh.db` in the backend working directory. This matters because some older instructions refer to `nutrisense.db`. Always check the active setting before deleting or inspecting a database.

The SQLite URL is created as:

```text
sqlite:///./<database filename>
```

The backend calls `Base.metadata.create_all()` in [main.py](nutrisense-auth/backend/app/main.py), so missing tables are created when the application starts. This is not a migration system; changing an existing table definition may require a fresh database or a proper migration process.

### Food data loading

For a quick local demonstration:

```powershell
cd nutrisense-auth\backend
venv\Scripts\activate
python -m app.seed_foods
```

For larger datasets, place the required raw files in the documented `app/data` folders and run the corresponding import module. The import scripts are designed to skip a source if it is already present, reducing duplicate imports.

The importer converts source-specific formats into the common `FoodItem` shape used by the application. It keeps only the nutrient columns required by this project instead of storing every column from a source dataset.

### Runtime model artifacts

The Assessment feature requires these files in `nutrisense-auth/backend/app/ml_artifacts/`:

```text
deficiency_model_random_forest.joblib
preprocess.joblib
meta.json
```

The backend loads these files in [assess_service.py](nutrisense-auth/backend/app/services/assess_service.py). If one is missing, the assessment endpoint returns a server error explaining that an artifact is missing.

## 5. Application pages and user journey

### Public pages

- `/`: landing page.
- `/login`: login form.
- `/signup`: account creation form.

### Protected pages

All of these are wrapped by [ProtectedRoute.jsx](nutrisense-auth/frontend/src/pages/ProtectedRoute.jsx), which redirects users without a token to `/`:

- `/onboarding`: create the health profile and dietary restrictions.
- `/dashboard`: overview of the user's nutrition information.
- `/food-diary`: search foods, choose a portion, add entries, and delete entries.
- `/lab-results`: save optional current lab values.
- `/assessment`: run or view the latest deficiency assessment and recommended foods.
- `/profile`: edit account/profile details.
- `/meal-plan`: generate and view a seven-day meal plan.
- `/progress`: view historical assessment progress.

Routes are declared in [App.jsx](nutrisense-auth/frontend/src/App.jsx).

### Recommended demonstration order

1. Start the backend and frontend.
2. Create an account.
3. Complete onboarding.
4. Log in again if onboarding signs the user out in the current UI flow.
5. Log food entries for breakfast, lunch, snack, and dinner on at least three complete dates within the assessment window.
6. Optionally enter lab values.
7. Run the assessment.
8. Explain the risks and recommended-food sections.
9. Generate the meal plan.
10. Open Progress after creating more than one assessment.

The application requires three complete diary days in the backend implementation. A complete day contains all four meal labels: breakfast, lunch, snack, and dinner.

## 6. Frontend architecture

### Routing

[App.jsx](nutrisense-auth/frontend/src/App.jsx) creates a `BrowserRouter`, registers public and protected routes, and wraps the application in `AuthProvider`.

React Router is used because this is a single-page application. Navigation changes the displayed component without full-page reloads.

### Authentication state

[AuthContext.jsx](nutrisense-auth/frontend/src/AuthContext.jsx) stores:

- `token`: JWT access token.
- `user`: basic user information.
- `logIn()`: updates React state and local storage.
- `logOut()`: clears React state and local storage.

The browser stores the token under `nutrisense_token` and the user under `nutrisense_user`. This keeps the user logged in across page refreshes, but it is a client-side storage approach and would need stronger security controls for a production system.

### API wrapper

[api.js](nutrisense-auth/frontend/src/api.js) centralizes `fetch` calls. `handleResponse()` parses JSON and converts backend errors into JavaScript `Error` objects. `authHeaders()` attaches the bearer token:

```text
Authorization: Bearer <JWT>
```

Centralizing requests prevents each page from duplicating URL construction, authentication headers, and error parsing.

### Shared navigation

[Sidebar.jsx](nutrisense-auth/frontend/src/pages/Sidebar.jsx) provides navigation for authenticated pages. It reads the current user and active route from the authentication context and React Router.

## 7. Backend architecture

### Application startup

[main.py](nutrisense-auth/backend/app/main.py) does the following:

1. Imports the database engine and declarative base.
2. Imports all SQLAlchemy models before table creation.
3. Creates missing tables.
4. Creates the FastAPI application.
5. Enables CORS for local Vite ports 5173 and 5174.
6. Includes all routers.
7. Exposes `/` and `/health` convenience endpoints.

The model imports are important because SQLAlchemy needs to know about all model classes before `create_all()` can create their tables.

### Database sessions

[database.py](nutrisense-auth/backend/app/database.py) creates a SQLAlchemy engine and a `SessionLocal` factory. `get_db()` yields one session per request and closes it in a `finally` block.

SQLite is configured with `check_same_thread=False` because FastAPI may handle work across request contexts. This is appropriate for this local demonstration but SQLite would not be the ideal database for a high-concurrency production deployment.

### Dependency injection

FastAPI dependencies are used for:

- Database sessions through `Depends(get_db)`.
- The authenticated user through `Depends(get_current_user)`.

This keeps authentication and resource cleanup consistent across endpoints.

## 8. Database schema

### `users`

Defined in [user.py](nutrisense-auth/backend/app/models/user.py).

- `id`: primary key.
- `first_name`, `last_name`: user display information.
- `email`: unique login identifier.
- `hashed_password`: bcrypt hash, never the plain password.
- `created_at`: creation timestamp.

### `health_profiles`

Defined in [health_profile.py](nutrisense-auth/backend/app/models/health_profile.py).

- `user_id`: one profile per user.
- `age`, `gender`, `height_cm`, `weight_kg`.
- `activity_level`, `health_goal`.
- `dietary_restrictions`: comma-separated normalized strings such as `vegetarian,gluten_free`.

The API accepts a list of restrictions, then the router stores that list as a string. This is a practical local representation, although a normalized many-to-many table or JSON column would be more flexible in production.

### `food_items`

Defined in [food_item.py](nutrisense-auth/backend/app/models/food_item.py).

Every row represents nutrient values per 100 grams:

- `calories_kcal`
- `protein_g`
- `iron_mg`
- `calcium_mg`
- `vitamin_d_mcg`
- `vitamin_b12_mcg`
- `folate_mcg`
- `vitamin_a_mcg`
- `vitamin_c_mg`
- `magnesium_mg`
- `zinc_mg`

The row also contains `source` and heuristic dietary fields:

- `is_vegetarian`
- `is_vegan`
- `contains_dairy`
- `contains_gluten`
- `contains_nuts`

The application stores a shared nutrient shape so diary calculations, model features, recommendations, and food search all use the same field names.

### `diary_entries`

Defined in [diary_entry.py](nutrisense-auth/backend/app/models/diary_entry.py).

- `user_id`: owner.
- `food_item_id`: selected food.
- `entry_date`: calendar date.
- `meal`: breakfast, lunch, snack, or dinner.
- `portion_grams`: user-entered quantity.
- `created_at`: entry timestamp.

The food nutrient values are not copied into the diary row. They are read from the referenced food item when totals are calculated or entries are displayed.

### `lab_results`

Defined in [lab_result.py](nutrisense-auth/backend/app/models/lab_result.py).

There is one current lab snapshot per user. All fields are optional:

- hemoglobin in g/dL.
- serum vitamin D.
- ferritin.
- vitamin B12.
- calcium.

Saving labs is an upsert rather than a history operation. This is intentional for the current interface, which represents the user's current values.

### `assessments`

Defined in [assessment.py](nutrisense-auth/backend/app/models/assessment.py).

- `features_json`: the feature dictionary used for the model.
- `risks_json`: the ten risk result objects.
- `overall_score`: wellness score from 0 to 100.
- `diary_days_used`: number of complete days used.
- `user_id`, `created_at`.

JSON is stored as text because this is a small SQLite application. The latest endpoint deserializes it before returning API data.

### `meal_plans`

Defined in [meal_plan.py](nutrisense-auth/backend/app/models/meal_plan.py).

- `user_id` and `assessment_id` identify ownership and source assessment.
- `dietary_restrictions` records restrictions used when generating the plan.
- `plan_json` stores the complete seven-day plan.
- `created_at` records creation time.

When a new plan is generated, the current user's previous plan is deleted and replaced.

## 9. Authentication and security flow

Authentication is implemented in [auth.py](nutrisense-auth/backend/app/auth.py) and [auth_router.py](nutrisense-auth/backend/app/routers/auth_router.py).

### Signup

1. The request is validated by Pydantic.
2. The backend checks whether the email already exists.
3. The password is hashed with bcrypt.
4. A user row is inserted.
5. A JWT is returned immediately with the new user.

### Login

1. The email is looked up.
2. The submitted password is verified against the bcrypt hash.
3. A JWT is created and returned.
4. The error message is intentionally vague when credentials fail, so the API does not reveal whether an email exists.

### JWT contents and validation

The token contains the user's email as the `sub` claim and an expiration time. The current configuration uses:

- Algorithm: HS256.
- Expiration: one day.
- Development secret stored in source code.

Every protected request passes through `get_current_user()`, which decodes the token, finds the user by the `sub` email, and rejects invalid, expired, or unknown-user tokens.

### Important production limitation

The secret key is explicitly a development secret. A production deployment must move it to a protected environment variable or secret manager, rotate it safely, use HTTPS, and consider a more robust token/storage strategy.

## 10. Food diary flow

The diary flow is implemented in [diary_router.py](nutrisense-auth/backend/app/routers/diary_router.py) and the UI is in [FoodDiary.jsx](nutrisense-auth/frontend/src/pages/FoodDiary.jsx).

### Search

The frontend debounces typing by 300 milliseconds and calls `/foods/search?q=...`.

The backend:

1. Finds names containing the query with a case-insensitive SQL `LIKE`.
2. Fetches a wider candidate pool.
3. Ranks exact matches first.
4. Then ranks names beginning with the query.
5. Then ranks names where the query is a separate word.
6. Uses name length and alphabetical order as tie-breakers.
7. Returns the requested limit.

This custom ranking makes a search such as `egg` more useful than alphabetical ordering alone.

### Adding an entry

The frontend sends food ID, date, meal, and portion grams. The backend validates the food exists and parses the date in `YYYY-MM-DD` format. It stores only the foreign key and user-entered portion.

### Nutrient scaling

Food values are stored per 100 grams. For a portion of `P` grams, the ratio is:

$$
ratio = \frac{P}{100}
$$

Each nutrient value is multiplied by that ratio. For example, if a food has 2 mg of iron per 100 g and the user logs 150 g:

$$
iron = 2 \times \frac{150}{100} = 3\text{ mg}
$$

The diary response returns scaled nutrient values for display.

## 11. Assessment and machine learning

The main implementation is in [assess_service.py](nutrisense-auth/backend/app/services/assess_service.py), exposed by [assess_router.py](nutrisense-auth/backend/app/routers/assess_router.py).

### Assessment prerequisites

The backend uses the last seven calendar days by default. It requires at least three distinct complete days. A complete day must contain all four required meal labels:

```text
breakfast, lunch, snack, dinner
```

This rule prevents an assessment from being based on only one incomplete day.

### Step 1: aggregate diary intake

For every diary entry in the window:

1. Join the entry to its food item.
2. Convert the portion to a ratio relative to 100 g.
3. Scale all eleven nutrition columns.
4. Add the scaled values to that date's totals.
5. Record the meal label for completeness checking.

Only complete dates are included in the average. If there are `D` complete days and `T_d` is a nutrient total for a day, the average is:

$$
average = \frac{\sum_{d=1}^{D} T_d}{D}
$$

### Step 2: build the feature vector

The model receives 13 features:

1. `gender`
2. `age_years`
3. `calories_kcal`
4. `protein_g`
5. `iron_mg`
6. `calcium_mg`
7. `vitamin_d_mcg`
8. `vitamin_b12_mcg`
9. `folate_mcg`
10. `vitamin_a_mcg`
11. `vitamin_c_mg`
12. `magnesium_mg`
13. `zinc_mg`

The feature order is important. The runtime reads the authoritative order from `ml_artifacts/meta.json` and creates a one-row pandas DataFrame before preprocessing.

### Step 3: preprocess and predict

The runtime loads:

- `deficiency_model_random_forest.joblib`.
- `preprocess.joblib`.
- `meta.json`.

The preprocessing artifact transforms the feature row exactly as expected by the trained model. The model predicts ten outputs, one for each deficiency label. For each output, the backend reads the probability of class `1`, interpreted as the probability of deficiency.

### Ten model outputs

```text
label_iron
label_vitamin_d
label_vitamin_b12
label_calcium
label_folate
label_vitamin_a
label_vitamin_c
label_magnesium
label_zinc
label_protein
```

The metadata is in [meta.json](nutrisense-auth/backend/app/ml_artifacts/meta.json).

### Step 4: optional laboratory boost

Laboratory values are not sent into the model as features. Instead, after the model prediction, selected low lab values can raise the corresponding risk to a minimum value:

- Low hemoglobin: iron risk at least 0.75.
- Low ferritin: iron risk at least 0.70.
- Low serum vitamin D: vitamin D risk at least 0.65.
- Low vitamin B12: vitamin B12 risk at least 0.60.
- Low calcium: calcium risk at least 0.55.

The comparison thresholds are implemented in `apply_lab_boost()`. The boost can increase a risk but does not lower the model result.

This is a hybrid design: the learned model estimates risk from diet and demographics, while optional lab information provides a deterministic safety-oriented adjustment.

### Step 5: display risk levels

The raw risk probability is returned as a percentage and a label:

- `HIGH` if probability is greater than 0.65.
- `MODERATE` if probability is at least 0.35.
- `LOW` otherwise.

The separate recommendation threshold is 0.45. Therefore, a nutrient can be eligible for recommendations while its visual level is `MODERATE`.

### Step 6: low-intake tags

The backend also compares average diary intake to simple reference thresholds. If intake is below the threshold, the UI receives a label such as `Low iron intake`.

These tags are not model predictions. They are a separate explanatory rule intended to help users understand possible low dietary intake.

### Step 7: wellness score

The wellness score uses all ten post-boost probabilities. If the average risk is `R`, the score is:

$$
wellness\ score = (1 - R) \times 100
$$

The result is rounded to one decimal place. A higher average predicted deficiency risk produces a lower wellness score.

This score is a project-level communication metric, not a clinically validated health score.

## 12. Recommended foods logic

Recommended foods are rule-based. The implementation is in [assess_service.py](nutrisense-auth/backend/app/services/assess_service.py), and the Assessment page displays the returned groups in [Assessment.jsx](nutrisense-auth/frontend/src/pages/Assessment.jsx).

### What the model does and does not do

The Random Forest answers:

```text
How likely is the user to be deficient in each supported nutrient?
```

It does not answer:

```text
Which foods should the user eat?
```

The recommendation stage uses the model's risk output as a trigger, then searches `food_items` using deterministic rules.

### Recommendation sequence

1. Read the risk objects from the assessment.
2. Keep risks with probability at least `0.45`.
3. Map the nutrient to its database column.
4. Rank candidates by source priority and nutrient amount per 100 g.
5. Take up to 48 candidates before final filtering.
6. Remove configured USDA noise names.
7. Apply the user's dietary restrictions through the existing heuristic tag logic.
8. Return up to six foods for the nutrient.
9. Keep a nutrient section even when its final food list is empty.

### Nutrient-to-column mapping

```text
iron       -> iron_mg
vitamin_d  -> vitamin_d_mcg
vitamin_b12 -> vitamin_b12_mcg
calcium    -> calcium_mg
folate     -> folate_mcg
vitamin_a  -> vitamin_a_mcg
vitamin_c  -> vitamin_c_mg
magnesium  -> magnesium_mg
zinc        -> zinc_mg
protein    -> protein_g
```

Values are per 100 g. Recommendations do not rescale values to a user's diary portion.

### Source priority

The current recommendation code gives this ordering:

1. `seed` or curated local rows.
2. `ifct` rows.
3. `usda` and `usda_sr_legacy` rows.
4. Unknown sources.

Within a source priority, foods with larger amounts of the selected nutrient rank first.

This preference makes the list more useful for the project's Indian-food context and reduces the chance that a generic USDA row dominates the display simply because it has a long or noisy name.

### USDA noise filtering

The recommendation logic excludes names containing terms such as:

```text
babyfood
candies
snacks
pie
puddings
salad dressing
refrigerated dough
food distribution program
artificial flavor
```

This is a name-based cleanup rule, not a clinical food-quality judgment.

### Dietary restriction filtering

Restrictions are normalized to supported values such as:

```text
vegetarian
vegan
gluten_free
dairy_free
nut_allergy
```

The existing [food_tags.py](nutrisense-auth/backend/app/services/food_tags.py) classifies names with keyword lists. For example:

- Meat and egg terms make a food non-vegetarian.
- Dairy terms make a food non-vegan.
- Wheat, bread, roti, pasta, and similar terms indicate possible gluten.
- Almond, peanut, cashew, and similar terms indicate possible nuts.

This is explicitly heuristic. It can under-block or over-block because the catalog does not provide a complete certified ingredient/allergen database.

### Recommendation API shape in this implementation

Recommendations are included in the assessment response:

```json
{
  "recommendations": {
    "calcium": [
      {"name": "Example food", "amount": 200.0}
    ],
    "iron": []
  }
}
```

The frontend renders one section per dictionary key and displays the nutrient-specific amount. The current application preserves this existing response shape for compatibility.

## 13. Meal-plan logic

Meal plans are separate from the Assessment recommendation cards. The implementation is in [meal_plan_service.py](nutrisense-auth/backend/app/services/meal_plan_service.py) and [meal_plan_router.py](nutrisense-auth/backend/app/routers/meal_plan_router.py).

### Generation prerequisites

A user must have a previous assessment. The service uses the latest assessment and the current health profile restrictions.

### Plan structure

- Seven days: Monday through Sunday.
- Four meals per day: breakfast, lunch, snack, dinner.
- Two food items per meal.
- Each selected food defaults to a 100 g portion.

### Selection approach

1. Load the latest assessment.
2. Select up to four focus nutrients using risks at or above 0.45, falling back to the highest risks if necessary.
3. Load foods allowed by the existing restrictions.
4. Rank foods using the combined values of the focus nutrient columns.
5. Build a reusable pool.
6. Rotate the starting position by day and meal to avoid showing exactly the same sequence repeatedly.
7. Avoid repeating the same food ID or primary food family on the same day.
8. Store the generated JSON and replace the previous plan.

### Existing-plan validation

When `/meal-plan/latest` loads a saved plan, it compares the restrictions stored with the plan to the current profile. It also rechecks each saved food against the current restrictions. If restrictions changed or a saved food is no longer allowed, the plan is regenerated.

This prevents an old plan from silently violating updated diet preferences.

## 14. REST API map

All protected endpoints require a bearer JWT unless stated otherwise.

### Authentication

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/signup` | Create an account and return a token |
| POST | `/auth/login` | Authenticate and return a token |
| GET | `/auth/me` | Return current user |
| PUT | `/auth/me` | Update user identity fields and return a new token |
| POST | `/auth/password` | Change password |

### Profile and labs

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/profile/onboarding` | Create or update health profile |
| GET | `/profile/me` | Get current health profile |
| PUT | `/profile/me` | Update current health profile |
| POST | `/labs` | Create or update current lab snapshot |
| GET | `/labs/me` | Get labs, returning empty values when none exist |

### Diary and foods

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/foods/search?q=...` | Search and relevance-rank catalog foods |
| POST | `/diary/entries` | Add a food diary entry |
| GET | `/diary/entries?entry_date=YYYY-MM-DD` | List one day's entries |
| DELETE | `/diary/entries/{entry_id}` | Delete an owned diary entry |

### Assessments

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/assess` | Run assessment, store it, and return risks/recommendations |
| GET | `/assess/latest` | Return latest assessment and recomputed recommendations |
| GET | `/assess/history` | Return assessment history metadata |

Recommendations are currently embedded in `/assess` and `/assess/latest`, not exposed as a separate endpoint.

### Meal plans

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/meal-plan/latest` | Return the saved plan or a not-found response |
| POST | `/meal-plan/regenerate` | Generate and save a new plan |

FastAPI generates interactive request and response documentation at `/docs`.

## 15. Model training and notebook work

The milestone notebooks document the research and training process. The runtime application does not download Kaggle, Hugging Face, or NHANES data when a user runs an assessment.

### Data acquisition shown in the notebook

The Milestone 2 notebook includes code for:

- Mounting Google Drive in Google Colab.
- Downloading a vitamin-deficiency dataset from Kaggle.
- Loading a food nutrition dataset from Hugging Face.
- Downloading NHANES 2017 and 2021 files.
- Reading SAS XPORT files with pandas.
- Combining demographic, dietary, CBC, vitamin D, and ferritin information.
- Restricting a dataset to adults from 18 through 65.
- Saving a merged Parquet dataset.

These steps are research/training preparation. They require external access and are not part of the local API request path.

### Feature and label design

The notebook defines the same 13 features and ten labels used by runtime metadata. This contract is important: if the feature names or order change during training but not in runtime, predictions can be incorrect or fail.

### Train/test split

The notebook uses an 80/20 train-test split with `random_state=42`. The fixed random state improves reproducibility of that split.

### Models compared

The notebook compares:

- Random Forest.
- XGBoost.
- LightGBM.
- CatBoost.

The model comparison metrics are stored in [metrics.json](nutrisense-auth/backend/app/ml_artifacts/metrics.json).

The metrics file reports LightGBM as the best model by the comparison summary, but the runtime artifact is named and configured as a Random Forest. This is an important review point: the application currently deploys the Random Forest artifact regardless of which model had the best comparison score.

### Reported metrics

The stored overall metrics are approximately:

| Model | Accuracy | Macro F1 | Micro F1 |
|---|---:|---:|---:|
| Random Forest | 0.9534 | 0.8261 | 0.9505 |
| XGBoost | 0.9522 | 0.8674 | 0.9503 |
| LightGBM | 0.9554 | 0.8681 | 0.9534 |
| CatBoost | 0.9545 | 0.8492 | 0.9521 |

Accuracy is high, but the per-nutrient results are uneven. The stored best per-nutrient F1 values are low for iron and vitamin D and extremely high for several other labels. A reviewer may ask about class imbalance, label construction, leakage, and whether the metric calculation reflects the real user population.

### Why use a saved artifact

Loading a serialized model is appropriate for a web application because:

- Training is expensive and does not belong in a user request.
- Predictions are fast.
- The same model can be used consistently until a new version is deployed.
- The preprocessing transform stays paired with the model.

The tradeoff is that artifact versioning and compatibility must be managed carefully.

## 16. Why each major design choice was made

### Why FastAPI?

FastAPI provides concise route definitions, automatic request validation, dependency injection, and generated OpenAPI documentation. It is a good fit for a Python ML-backed API because the model and pandas ecosystem are already Python-based.

### Why React?

React breaks the user interface into reusable pages and components and allows the dashboard to update from API responses without full-page navigation.

### Why SQLite?

SQLite has no separate database server, is easy to run locally, and is sufficient for a student demonstration. It is not selected for large-scale concurrent production workloads.

### Why SQLAlchemy?

SQLAlchemy maps Python model classes to relational tables and provides parameterized database queries. This is easier to maintain than writing SQL strings throughout every route.

### Why JWT?

JWTs allow the backend to verify a user's identity on each request without storing a server-side session object. The current implementation is simple for a local SPA, though token storage and secret management need hardening in production.

### Why bcrypt?

Passwords should never be stored in plain text. Bcrypt is intentionally slow and salted, making password-guessing attacks more expensive.

### Why aggregate several diary days?

A single day can be unusual. Averaging complete days produces a more stable representation of typical intake and avoids treating a partial diary as a full nutritional profile.

### Why keep recommendations rule-based?

A deterministic nutrient lookup is easier to explain and audit than asking the model to generate food suggestions. It also makes the distinction clear: ML estimates risk; rules select nutrient-rich foods that match preferences.

### Why per-100-gram nutrient values?

A common unit makes foods comparable. Portion scaling is then a simple ratio, and the same values can be used by the diary, recommendations, and model feature calculations.

### Why optional lab boosts instead of model inputs?

The current model was trained on the defined feature vector. Adding lab columns at runtime without retraining would violate the model contract. The post-prediction boost uses lab information without changing the trained feature shape.

## 17. Limitations and honest review points

These are useful points to mention proactively during a review.

1. **Not a medical diagnostic tool.** Predictions are educational and should not replace professional medical evaluation.
2. **Model quality is label-dependent.** High aggregate accuracy can hide weak performance for specific nutrients, especially iron and vitamin D.
3. **The model is trained from a fixed dataset.** It may not generalize to every age, culture, disease state, or dietary pattern.
4. **Food restrictions are heuristic.** Name-based keyword classification cannot replace certified ingredient or allergen labeling.
5. **The database is local SQLite.** It is convenient for a demonstration but not ideal for multi-user production scale.
6. **The JWT secret is development-only.** It must be moved out of source code for deployment.
7. **CORS is configured for localhost.** Production origins should be explicitly configured.
8. **There is no migration framework.** Schema changes require care and may need a fresh database.
9. **Lab data is a current snapshot.** The current schema does not maintain lab history.
10. **Recommendations use stored per-100-gram values.** They do not automatically account for a user's calorie target, medical restrictions beyond supported tags, cooking context, or portion size.
11. **Meal plans are deterministic rules, not an optimizer.** They do not calculate a full daily calorie target or guarantee recommended dietary allowances.
12. **Model artifact choice should be clarified.** The metrics summary names LightGBM as best, while the deployed artifact is Random Forest.
13. **No automated test suite is visible in the repository.** Manual API and UI checks are currently important.

## 18. Common review questions and strong answers

### What is the input to the model?

A 13-feature row containing gender, age, and average daily calories, protein, iron, calcium, vitamin D, vitamin B12, folate, vitamin A, vitamin C, magnesium, and zinc.

### What is the output?

Ten deficiency probabilities, one for each supported nutrient. The backend also converts them into percentages, HIGH/MODERATE/LOW display levels, and a wellness score.

### Why does the model need preprocessing?

The saved preprocessing artifact guarantees that inference applies the same transformations expected during training. The model should not receive an ad hoc feature format.

### How are probabilities obtained?

The backend calls `predict_proba()` and takes the probability of class `1`, which represents deficient.

### What does the 45% threshold mean?

It is the deterministic cutoff for showing a recommendation group. It is separate from the 50% `predicted_deficient` flag and the UI level thresholds.

### Is food recommendation machine learning?

No. Food recommendation is a rule-based database lookup. The model provides the risk signal; nutrient-column ranking and diet filtering provide the food list.

### How is a diary portion handled?

Food values are per 100 g. The backend multiplies every nutrient by `portion_grams / 100` before returning scaled diary values or aggregating an assessment.

### Why require three complete days?

To reduce the effect of a single unusual day and avoid assessing a profile with missing meal categories.

### Why are labs not model features?

The trained model expects 13 specific features. Labs are applied afterward as a controlled risk adjustment so the model input contract remains unchanged.

### What happens when a user changes dietary restrictions?

New assessments recompute recommendations using current restrictions. Existing meal plans are checked against current restrictions and regenerated if they are no longer compatible.

### How does the app prevent a user from reading another user's data?

Protected routes require a valid JWT. Backend queries use `current_user.id` when reading or mutating profiles, diary entries, assessments, labs, and meal plans.

### Why use both frontend protection and backend authentication?

Frontend protection improves user experience by redirecting unauthenticated users. Backend authentication is the real security boundary because clients can bypass frontend code.

### What happens if model files are missing?

The backend raises a `FileNotFoundError`, and the assessment route converts it into an HTTP 500 response explaining which artifact is missing.

### Why is a saved assessment stored if recommendations are rule-based?

The assessment stores the model inputs, risk results, score, and number of diary days for history and progress. Recommendations can be recomputed from the latest risks and current food/restriction rules.

### Why can a nutrient's recommendation list contain zero values?

Some source datasets do not measure every nutrient for every food. For example, IFCT rows may have zero vitamin B12. The rule engine selects the highest available values among allowed candidates, which can still be zero.

## 19. Practical troubleshooting

### `ModuleNotFoundError`

Activate the backend virtual environment and run commands from `nutrisense-auth/backend`.

```powershell
venv\Scripts\activate
```

### Frontend cannot reach the backend

Check that:

1. Uvicorn is running on port 8000.
2. The frontend is using the same API base URL.
3. The request includes a valid token for protected endpoints.
4. CORS allows the frontend port.

### Assessment returns insufficient diary data

Log breakfast, lunch, snack, and dinner on at least three distinct dates inside the last seven days.

### Assessment returns missing artifact error

Verify that all three files exist in `backend/app/ml_artifacts`:

```text
deficiency_model_random_forest.joblib
preprocess.joblib
meta.json
```

### Food search returns no useful foods

Check that the food import or seed command has populated the active database, and verify the database filename selected by `NUTRISENSE_DATABASE_FILE`.

### Duplicate food imports

The import scripts check whether their source is already loaded. If a fresh import is genuinely required, stop the backend first and use a backup or a deliberate database reset.

### Port already in use

Stop the old Uvicorn/Vite process or use a different port. If the frontend moves to another port, update CORS if it is not already listed.

## 20. Suggested review demonstration

A clear five-minute demonstration can follow this sequence:

1. Show the architecture diagram and explain the ML/rules separation.
2. Sign up and point out bcrypt hashing and JWT authentication.
3. Complete the profile and explain why dietary preferences affect recommendations.
4. Search a food and log a portion; explain per-100-gram scaling.
5. Run the assessment; explain the seven-day window, complete-day requirement, 13 features, and ten probabilities.
6. Show a lab value and explain the post-prediction boost.
7. Open Recommended foods; explain the 45% cutoff, nutrient-column ranking, source priority, noise filtering, and six-food limit.
8. Generate the meal plan and explain that it is a separate deterministic service.
9. Show Progress and explain why assessments are stored historically.
10. Close with limitations: educational use, heuristic allergens, model generalization, and development-only security configuration.

## 21. Files to open during a code review

For the fastest code walkthrough, open these files in order:

1. [main.py](nutrisense-auth/backend/app/main.py): application startup, CORS, routers, table creation.
2. [database.py](nutrisense-auth/backend/app/database.py): SQLite engine and sessions.
3. [auth_router.py](nutrisense-auth/backend/app/routers/auth_router.py): signup, login, JWT-protected user dependency.
4. [diary_router.py](nutrisense-auth/backend/app/routers/diary_router.py): portion scaling and diary CRUD.
5. [assess_service.py](nutrisense-auth/backend/app/services/assess_service.py): aggregation, model inference, lab boost, score, recommendations.
6. [assess_router.py](nutrisense-auth/backend/app/routers/assess_router.py): persistence and assessment endpoints.
7. [food_tags.py](nutrisense-auth/backend/app/services/food_tags.py): dietary heuristic rules.
8. [meal_plan_service.py](nutrisense-auth/backend/app/services/meal_plan_service.py): seven-day plan generation.
9. [api.js](nutrisense-auth/frontend/src/api.js): frontend API contract.
10. [App.jsx](nutrisense-auth/frontend/src/App.jsx): frontend routes.
11. [Assessment.jsx](nutrisense-auth/frontend/src/pages/Assessment.jsx): risk and recommendation presentation.
12. [meta.json](nutrisense-auth/backend/app/ml_artifacts/meta.json): deployed model contract.
13. [metrics.json](nutrisense-auth/backend/app/ml_artifacts/metrics.json): model comparison results.

## 22. Final summary to memorize

NutriSense is a React and FastAPI nutrition application backed by SQLite. Users create a profile, log foods and portions, and optionally enter labs. The backend converts portions into nutrient totals, averages complete diary days, and sends 13 ordered features through saved preprocessing and a deployed Random Forest. The model returns ten deficiency probabilities. Optional labs can raise selected risks after prediction. The wellness score is one minus the average risk, expressed as a percentage. Recommended foods are not generated by the model; they are rule-based lookups ranked by nutrient amount and source priority, filtered by heuristic dietary restrictions, and limited to six foods per high-risk nutrient. Meal plans are a separate deterministic seven-day service. The project is designed for education and demonstration, so security, medical validity, scalability, allergen accuracy, and model generalization would require further work before production use.
