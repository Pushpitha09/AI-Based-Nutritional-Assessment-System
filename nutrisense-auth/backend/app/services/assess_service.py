"""
Implements the assessment flow:

    diary_entries
        -> complete diary days
        -> daily nutrient totals
        -> average per day
        -> combine with age + gender
        -> 13 features
        -> Random Forest predict_proba
        -> 10 deficiency probabilities
        -> optional lab boost
        -> wellness score
        -> recommended foods for high-risk nutrients

IMPORTANT:
Recommendation filtering and scoring do NOT change the ML model,
assessment probabilities, or wellness score calculation.
"""

from datetime import date, timedelta
from pathlib import Path
import json
import re

import joblib
import pandas as pd
from sqlalchemy.orm import Session

from app.models.diary_entry import DiaryEntry
from app.models.food_item import FoodItem
from app.models.health_profile import HealthProfile
from app.models.lab_result import LabResult

from app.services.food_tags import (
    food_matches_restrictions,
    normalize_restrictions,
    is_good_recommendation_food,
    food_quality_score,
    get_food_key,
)


ARTIFACTS_DIR = Path(__file__).parent.parent / "ml_artifacts"

MIN_DIARY_DAYS = 3
DEFAULT_WINDOW_DAYS = 7

REQUIRED_MEALS = {
    "breakfast",
    "lunch",
    "snack",
    "dinner",
}


DIARY_NUTRIENT_COLS = [
    "calories_kcal",
    "protein_g",
    "iron_mg",
    "calcium_mg",
    "vitamin_d_mcg",
    "vitamin_b12_mcg",
    "folate_mcg",
    "vitamin_a_mcg",
    "vitamin_c_mg",
    "magnesium_mg",
    "zinc_mg",
]


RDA_THRESHOLDS = {
    "iron_mg": 8,
    "vitamin_d_mcg": 15,
    "vitamin_b12_mcg": 2.4,
    "calcium_mg": 1000,
    "folate_mcg": 400,
    "vitamin_a_mcg": 700,
    "vitamin_c_mg": 75,
    "magnesium_mg": 320,
    "zinc_mg": 8,
    "protein_g": 50,
}


LABEL_TO_NUTRIENT_COL = {
    "label_iron": "iron_mg",
    "label_vitamin_d": "vitamin_d_mcg",
    "label_vitamin_b12": "vitamin_b12_mcg",
    "label_calcium": "calcium_mg",
    "label_folate": "folate_mcg",
    "label_vitamin_a": "vitamin_a_mcg",
    "label_vitamin_c": "vitamin_c_mg",
    "label_magnesium": "magnesium_mg",
    "label_zinc": "zinc_mg",
    "label_protein": "protein_g",
}


RECOMMENDATION_THRESHOLD = 0.45
RECOMMENDATIONS_PER_NUTRIENT = 6


# ================================================================
# Recommendation configuration
# ================================================================

# The IFCT micronutrient values in the current database use a
# different scale from the USDA-style entries.
#
# This conversion is used ONLY for recommendation ranking/display.
# It is NOT used in diary calculations or ML predictions.
IFCT_MICRONUTRIENT_COLUMNS = {
    "iron_mg",
    "calcium_mg",
    "vitamin_d_mcg",
    "vitamin_b12_mcg",
    "folate_mcg",
    "vitamin_a_mcg",
    "vitamin_c_mg",
    "magnesium_mg",
    "zinc_mg",
}


REFERENCE_VALUES = {
    "iron_mg": 18,
    "vitamin_d_mcg": 20,
    "vitamin_b12_mcg": 4,
    "calcium_mg": 1000,
    "folate_mcg": 400,
    "vitamin_a_mcg": 900,
    "vitamin_c_mg": 90,
    "magnesium_mg": 420,
    "zinc_mg": 11,
    "protein_g": 50,
}


# These keywords ONLY classify existing database foods.
# They do not add or create foods.
PRACTICAL_FOOD_KEYWORDS = {

    "iron_mg": [
        "lentil",
        "dal",
        "chickpea",
        "chana",
        "rajma",
        "kidney bean",
        "black gram",
        "urad",
        "green gram",
        "moong",
        "mung",
        "soybean",
        "tofu",
        "spinach",
        "amaranth",
        "sesame",
        "pumpkin seed",
        "egg",
        "sardine",
        "tuna",
        "mackerel",
    ],

    "calcium_mg": [
        "ragi",
        "finger millet",
        "tofu",
        "sesame",
        "amaranth",
        "spinach",
        "soybean",
        "soymilk",
        "soy milk",
        "fortified cereal",
        "fortified soy milk",
        "milk",
        "curd",
        "yogurt",
        "yoghurt",
        "paneer",
        "cheese",
    ],

    "vitamin_d_mcg": [
        "egg",
        "egg yolk",
        "salmon",
        "sardine",
        "mackerel",
        "trout",
        "tuna",
        "fish",
        "fortified cereal",
        "fortified milk",
        "fortified soy milk",
        "soymilk",
        "soy milk",
        "mushroom",
    ],

    "vitamin_b12_mcg": [
        "egg",
        "milk",
        "curd",
        "yogurt",
        "yoghurt",
        "paneer",
        "cheese",
        "soymilk",
        "soy milk",
        "fortified cereal",
        "fortified",
        "nutritional yeast",
    ],

    "folate_mcg": [
        "spinach",
        "amaranth",
        "drumstick",
        "lentil",
        "dal",
        "chickpea",
        "chana",
        "green gram",
        "moong",
        "peas",
        "bean",
        "orange",
        "papaya",
        "guava",
        "avocado",
    ],

    "vitamin_a_mcg": [
        "carrot",
        "spinach",
        "amaranth",
        "sweet potato",
        "pumpkin",
        "papaya",
        "mango",
        "tomato",
        "capsicum",
        "bell pepper",
        "egg",
    ],

    "vitamin_c_mg": [
        "guava",
        "amla",
        "gooseberry",
        "orange",
        "lemon",
        "papaya",
        "tomato",
        "capsicum",
        "bell pepper",
        "broccoli",
        "kiwi",
        "strawberry",
    ],

    "magnesium_mg": [
        "ragi",
        "finger millet",
        "sesame",
        "pumpkin seed",
        "almond",
        "cashew",
        "walnut",
        "chickpea",
        "chana",
        "lentil",
        "dal",
        "spinach",
        "oats",
        "soybean",
        "tofu",
    ],

    "zinc_mg": [
        "sesame",
        "pumpkin seed",
        "chickpea",
        "chana",
        "lentil",
        "dal",
        "soybean",
        "tofu",
        "paneer",
        "egg",
        "oats",
        "cashew",
        "almond",
    ],

    "protein_g": [
        "egg",
        "milk",
        "curd",
        "yogurt",
        "yoghurt",
        "paneer",
        "tofu",
        "soybean",
        "lentil",
        "dal",
        "chickpea",
        "chana",
        "rajma",
        "kidney bean",
        "green gram",
        "moong",
        "peas",
    ],
}


# Foods that shouldn't normally appear as everyday
# NutriSense recommendations.
UNSUITABLE_RECOMMENDATION_TERMS = (
    " raw",
    ", raw",
    "raw,",
    "liver",
    "kidney",
    "giblet",
    "gizzard",
    "heart",
    "tongue",
    "tripe",
    "brain",
    "liverwurst",
    "braunschweiger",
    "liver sausage",
    "liver cheese",
    "pate",
    "powder",
    "dry mix",
    "unprepared",
    "not reconstituted",
    "spices,",
    "paprika",
    "marjoram",
    "spearmint",
    "chives",
    "baking powder",
    "leavening agent",
    "salt substitute",
    "food additive",
    "food coloring",
    "food colouring",
    "flavoring",
    "flavouring",
    "yeast extract",
    "babyfood",
    "baby food",
    "infant formula",
    "toddler",
    "candies",
    "candy",
    "pie",
    "pudding",
    "puddings",
    "salad dressing",
    "refrigerated dough",
    "tablet",
    "supplement",
    "food distribution program",
    "artificial flavor",
    "artificial flavour",
    "margarine",
    "whey, acid",
    "caramel-coated",
    "confection",
    "heavy syrup",
    "syrup, solids",
)


# ================================================================
# Food filtering helpers
# ================================================================

def _is_unsuitable_recommendation_food(name: str) -> bool:

    name_lower = (
        name or ""
    ).casefold()

    return any(
        term in name_lower
        for term in UNSUITABLE_RECOMMENDATION_TERMS
    )


def _keyword_match_score(
    name: str,
    nutrient_col: str,
) -> int:
    """
    Counts how strongly a food matches practical foods
    for a particular nutrient.
    """

    text = (
        name or ""
    ).casefold()

    keywords = PRACTICAL_FOOD_KEYWORDS.get(
        nutrient_col,
        [],
    )

    score = 0

    for keyword in keywords:

        pattern = (
            r"\b"
            + re.escape(
                keyword.casefold()
            )
            + r"\b"
        )

        if re.search(
            pattern,
            text,
        ):
            score += 1

    return score


def _recommendation_family(
    name: str,
) -> str:
    """
    Groups database records into practical food families.

    Example:

        SILK Vanilla, soymilk
        SILK Chocolate, soymilk
        SILK Unsweetened, soymilk

    all become:

        soy milk

    Likewise, different tofu products become:

        tofu
    """

    text = (
        name or ""
    ).casefold()

    family_rules = {

        "soy milk": (
            "soymilk",
            "soy milk",
        ),

        "tofu": (
            "tofu",
        ),

        "yogurt": (
            "yogurt",
            "yoghurt",
        ),

        "curd": (
            "curd",
        ),

        "milk": (
            "milk",
        ),

        "paneer": (
            "paneer",
        ),

        "cheese": (
            "cheese",
        ),

        "lentils": (
            "lentil",
            "dal",
        ),

        "chickpeas": (
            "chickpea",
            "chana",
            "garbanzo",
        ),

        "beans": (
            "rajma",
            "kidney bean",
            "black bean",
            "green bean",
            "beans",
        ),

        "green gram": (
            "green gram",
            "moong",
            "mung",
        ),

        "spinach": (
            "spinach",
        ),

        "amaranth": (
            "amaranth",
        ),

        "carrot": (
            "carrot",
        ),

        "papaya": (
            "papaya",
        ),

        "mango": (
            "mango",
        ),

        "guava": (
            "guava",
        ),

        "orange": (
            "orange",
        ),

        "tomato": (
            "tomato",
        ),

        "ragi": (
            "ragi",
            "finger millet",
        ),

        "sesame": (
            "sesame",
        ),

        "pumpkin seeds": (
            "pumpkin seed",
        ),

        "almond": (
            "almond",
        ),

        "cashew": (
            "cashew",
        ),

        "walnut": (
            "walnut",
        ),

        "oats": (
            "oat",
            "oatmeal",
        ),

        "egg": (
            "egg",
        ),

        "sardine": (
            "sardine",
        ),

        "salmon": (
            "salmon",
        ),

        "mackerel": (
            "mackerel",
        ),

        "trout": (
            "trout",
        ),

        "tuna": (
            "tuna",
        ),

        "sweet potato": (
            "sweet potato",
        ),

        "pumpkin": (
            "pumpkin",
        ),

        "peas": (
            "peas",
        ),

        "broccoli": (
            "broccoli",
        ),

        "capsicum": (
            "capsicum",
            "bell pepper",
        ),

        "mushroom": (
            "mushroom",
        ),

        "fortified cereal": (
            "fortified cereal",
            "breakfast cereal",
        ),
    }

    for family, keywords in family_rules.items():

        for keyword in keywords:

            if keyword in text:
                return family

    # Fallback for foods that aren't covered above.
    primary = (
        text
        .split(",", 1)[0]
        .strip()
    )

    return re.sub(
        r"[^a-z0-9]+",
        " ",
        primary,
    ).strip()


def _food_category_score(
    name: str,
) -> int:
    """
    General practicality score.
    """

    text = (
        name or ""
    ).casefold()

    very_practical = (
        "ragi",
        "finger millet",
        "lentil",
        "dal",
        "chickpea",
        "chana",
        "rajma",
        "kidney bean",
        "green gram",
        "moong",
        "spinach",
        "amaranth",
        "carrot",
        "tomato",
        "orange",
        "guava",
        "papaya",
        "mango",
        "banana",
        "apple",
        "tofu",
        "soybean",
        "sesame",
        "pumpkin seed",
        "oats",
        "egg",
        "milk",
        "curd",
        "yogurt",
        "paneer",
    )

    practical = (
        "peas",
        "beans",
        "broccoli",
        "capsicum",
        "sweet potato",
        "pumpkin",
        "almond",
        "cashew",
        "walnut",
        "chia",
        "flaxseed",
        "fortified cereal",
        "soy milk",
        "soymilk",
    )

    if any(
        word in text
        for word in very_practical
    ):
        return 3

    if any(
        word in text
        for word in practical
    ):
        return 2

    return 0


# ================================================================
# Recommendation nutrient handling
# ================================================================

def _recommendation_nutrient_value(
    food: FoodItem,
    nutrient_col: str,
) -> float:
    """
    Gets a source-aware nutrient value for recommendations.

    IMPORTANT:
    This is ONLY for recommendation ranking/display.
    It is NOT used in the ML assessment.
    """

    value = float(
        getattr(
            food,
            nutrient_col,
            0,
        )
        or 0
    )

    value = max(
        value,
        0,
    )

    source = str(
        getattr(
            food,
            "source",
            "",
        )
        or ""
    ).casefold()

    if (
        source == "ifct"
        and nutrient_col
        in IFCT_MICRONUTRIENT_COLUMNS
    ):
        value *= 1000

    return value


def _nutrient_score(
    value: float,
    nutrient_col: str,
) -> float:

    reference = REFERENCE_VALUES.get(
        nutrient_col,
        100,
    )

    if reference <= 0:
        return 0

    percentage = (
        value / reference
    ) * 100

    return min(
        percentage,
        100,
    )


def _recommendation_score(
    food: FoodItem,
    nutrient_col: str,
) -> tuple:

    value = _recommendation_nutrient_value(
        food,
        nutrient_col,
    )

    keyword_score = _keyword_match_score(
        food.name,
        nutrient_col,
    )

    category_score = _food_category_score(
        food.name,
    )

    quality_score = food_quality_score(
        food.name,
    )

    nutrient_score = _nutrient_score(
        value,
        nutrient_col,
    )

    # Practical food relevance comes first.
    #
    # This prevents a database product with a high
    # nutrient number from automatically beating a
    # normal everyday food.
    return (
        keyword_score,
        category_score,
        quality_score,
        nutrient_score,
        food.name.casefold(),
    )


# ================================================================
# Recommended foods
# ================================================================

def get_recommended_foods(
    db: Session,
    profile: HealthProfile,
    nutrient_col: str,
    limit: int = RECOMMENDATIONS_PER_NUTRIENT,
):
    """
    Returns practical and diverse food recommendations.

    All foods come from the existing FoodItem database.
    """

    restrictions = []

    if (
        profile
        and profile.dietary_restrictions
    ):

        restrictions = normalize_restrictions(
            profile.dietary_restrictions.split(",")
        )

    nutrient_field = getattr(
        FoodItem,
        nutrient_col,
    )

    candidates = (
        db.query(FoodItem)
        .filter(
            nutrient_field.isnot(None)
        )
        .filter(
            nutrient_field > 0
        )
        .all()
    )

    suitable = []

    for food in candidates:

        if not food.name:
            continue

        if not is_good_recommendation_food(
            food.name
        ):
            continue

        if _is_unsuitable_recommendation_food(
            food.name
        ):
            continue

        if not food_matches_restrictions(
            food,
            restrictions,
        ):
            continue

        suitable.append(food)

    # ------------------------------------------------------------
    # Prefer foods that are specifically useful for this nutrient.
    # ------------------------------------------------------------

    practical = [
        food
        for food in suitable
        if _keyword_match_score(
            food.name,
            nutrient_col,
        ) > 0
    ]

    if len(practical) >= limit:
        candidates = practical
    else:
        candidates = suitable

    candidates.sort(
        key=lambda food: _recommendation_score(
            food,
            nutrient_col,
        ),
        reverse=True,
    )

    results = []

    seen_database_keys = set()
    seen_families = set()

    # ------------------------------------------------------------
    # First pass:
    # one food per practical family
    # ------------------------------------------------------------

    for food in candidates:

        food_key = get_food_key(
            food.name
        )

        if food_key in seen_database_keys:
            continue

        family = _recommendation_family(
            food.name
        )

        if family in seen_families:
            continue

        amount = _recommendation_nutrient_value(
            food,
            nutrient_col,
        )

        if amount <= 0:
            continue

        results.append(
            {
                "name": food.name,
                "amount": round(
                    amount,
                    2,
                ),
            }
        )

        seen_database_keys.add(
            food_key
        )

        seen_families.add(
            family
        )

        if len(results) >= limit:
            break

    # ------------------------------------------------------------
    # IMPORTANT:
    #
    # We deliberately do NOT fill missing slots with duplicates.
    #
    # If there are only 3 genuinely different suitable food
    # families, return 3.
    # ------------------------------------------------------------

    return results


def build_recommendations(
    db,
    user_id,
    risk_items,
):

    profile = (
        db.query(HealthProfile)
        .filter(
            HealthProfile.user_id == user_id
        )
        .first()
    )

    recommendations = {}

    high_risk_items = sorted(
        (
            risk
            for risk in risk_items
            if risk["probability"]
            >= RECOMMENDATION_THRESHOLD
        ),
        key=lambda risk: risk["probability"],
        reverse=True,
    )

    for risk in high_risk_items:

        nutrient_col = (
            LABEL_TO_NUTRIENT_COL[
                risk["label"]
            ]
        )

        recommendations[
            risk["nutrient"]
        ] = get_recommended_foods(
            db,
            profile,
            nutrient_col,
        )

    return recommendations


# ================================================================
# ML artifact loading
# ================================================================

class AssessmentError(Exception):
    pass


def _load_artifacts():

    model_path = (
        ARTIFACTS_DIR
        / "deficiency_model_random_forest.joblib"
    )

    preprocess_path = (
        ARTIFACTS_DIR
        / "preprocess.joblib"
    )

    meta_path = (
        ARTIFACTS_DIR
        / "meta.json"
    )

    for path in (
        model_path,
        preprocess_path,
        meta_path,
    ):

        if not path.exists():

            raise FileNotFoundError(
                f"Missing model artifact: {path}. "
                "Place deficiency_model_random_forest.joblib, "
                "preprocess.joblib, and meta.json "
                "in backend/app/ml_artifacts/"
            )

    model = joblib.load(
        model_path
    )

    preprocess = joblib.load(
        preprocess_path
    )

    with open(
        meta_path,
        encoding="utf-8",
    ) as file:

        meta = json.load(
            file
        )

    return (
        model,
        preprocess,
        meta,
    )


# ================================================================
# Diary processing
# ================================================================

def get_diary_summary(
    db,
    user_id,
    window_days=DEFAULT_WINDOW_DAYS,
):

    since = (
        date.today()
        - timedelta(
            days=window_days - 1
        )
    )

    rows = (
        db.query(
            DiaryEntry,
            FoodItem,
        )
        .join(
            FoodItem,
            DiaryEntry.food_item_id
            == FoodItem.id,
        )
        .filter(
            DiaryEntry.user_id == user_id,
            DiaryEntry.entry_date >= since,
        )
        .all()
    )

    daily_totals = {}
    daily_meals = {}

    for entry, food in rows:

        ratio = (
            entry.portion_grams
            / 100.0
        )

        day = entry.entry_date

        if day not in daily_totals:

            daily_totals[day] = {
                col: 0.0
                for col
                in DIARY_NUTRIENT_COLS
            }

            daily_meals[day] = set()

        daily_meals[day].add(
            str(
                entry.meal
            ).lower()
        )

        for col in DIARY_NUTRIENT_COLS:

            value = (
                getattr(
                    food,
                    col,
                )
                or 0
            )

            daily_totals[day][col] += (
                value * ratio
            )

    complete_days = {
        day: totals
        for day, totals
        in daily_totals.items()
        if REQUIRED_MEALS.issubset(
            daily_meals[day]
        )
    }

    distinct_days = len(
        complete_days
    )

    if distinct_days < MIN_DIARY_DAYS:

        raise AssessmentError(
            f"Need at least {MIN_DIARY_DAYS} days "
            "with breakfast, lunch, snack, and dinner "
            f"logged in the last {window_days} days "
            f"(found {distinct_days} complete days)."
        )

    averages = {
        col: 0.0
        for col
        in DIARY_NUTRIENT_COLS
    }

    for day_totals in (
        complete_days.values()
    ):

        for col in DIARY_NUTRIENT_COLS:

            averages[col] += (
                day_totals[col]
            )

    for col in DIARY_NUTRIENT_COLS:

        averages[col] /= (
            distinct_days
        )

    return {
        "averages": averages,
        "distinct_days": distinct_days,
    }


def build_feature_dict(
    db,
    user_id,
    diary_averages,
):

    profile = (
        db.query(HealthProfile)
        .filter(
            HealthProfile.user_id == user_id
        )
        .first()
    )

    if not profile:

        raise AssessmentError(
            "Complete your health profile "
            "(onboarding) before running an assessment."
        )

    features = {
        "gender": profile.gender,
        "age_years": profile.age,
    }

    features.update(
        diary_averages
    )

    return features


# ================================================================
# Lab results
# ================================================================

def apply_lab_boost(
    db,
    user_id,
    risk_by_label,
):

    labs = (
        db.query(LabResult)
        .filter(
            LabResult.user_id == user_id
        )
        .first()
    )

    if not labs:
        return risk_by_label

    profile = (
        db.query(HealthProfile)
        .filter(
            HealthProfile.user_id == user_id
        )
        .first()
    )

    is_female = (
        profile is not None
        and profile.gender == 2
    )

    boosted = dict(
        risk_by_label
    )

    if (
        labs.hemoglobin_g_dl
        is not None
    ):

        low_hgb = (
            labs.hemoglobin_g_dl
            < (
                12
                if is_female
                else 13
            )
        )

        if low_hgb:

            boosted[
                "label_iron"
            ] = max(
                boosted.get(
                    "label_iron",
                    0,
                ),
                0.75,
            )

    if (
        labs.ferritin is not None
        and labs.ferritin < 30
    ):

        boosted[
            "label_iron"
        ] = max(
            boosted.get(
                "label_iron",
                0,
            ),
            0.70,
        )

    if (
        labs.serum_vitamin_d
        is not None
        and labs.serum_vitamin_d < 50
    ):

        boosted[
            "label_vitamin_d"
        ] = max(
            boosted.get(
                "label_vitamin_d",
                0,
            ),
            0.65,
        )

    if (
        labs.vitamin_b12
        is not None
        and labs.vitamin_b12 < 200
    ):

        boosted[
            "label_vitamin_b12"
        ] = max(
            boosted.get(
                "label_vitamin_b12",
                0,
            ),
            0.60,
        )

    if (
        labs.calcium is not None
        and labs.calcium < 8.5
    ):

        boosted[
            "label_calcium"
        ] = max(
            boosted.get(
                "label_calcium",
                0,
            ),
            0.55,
        )

    return boosted


# ================================================================
# Assessment helpers
# ================================================================

def ui_level(
    probability,
):

    if probability > 0.65:
        return "HIGH"

    if probability >= 0.35:
        return "MODERATE"

    return "LOW"


def calculate_wellness_score(
    probabilities,
):

    if not probabilities:

        raise ValueError(
            "At least one deficiency probability is required"
        )

    average_risk = (
        sum(probabilities)
        / len(probabilities)
    )

    return round(
        (1 - average_risk)
        * 100,
        1,
    )


# ================================================================
# Main assessment
# ================================================================

def run_assessment(
    db,
    user_id,
    window_days=DEFAULT_WINDOW_DAYS,
):

    # ------------------------------------------------------------
    # Load ML artifacts
    # ------------------------------------------------------------

    (
        model,
        preprocess,
        meta,
    ) = _load_artifacts()

    feature_order = meta[
        "features"
    ]

    label_order = meta[
        "labels"
    ]

    # ------------------------------------------------------------
    # Diary
    # ------------------------------------------------------------

    diary = get_diary_summary(
        db,
        user_id,
        window_days,
    )

    feature_dict = build_feature_dict(
        db,
        user_id,
        diary["averages"],
    )

    # ------------------------------------------------------------
    # ML prediction
    # ------------------------------------------------------------

    X = pd.DataFrame(
        [feature_dict]
    )[feature_order]

    X_processed = (
        preprocess.transform(X)
    )

    proba_list = (
        model.predict_proba(
            X_processed
        )
    )

    risk_by_label = {}

    for i, label in enumerate(
        label_order
    ):

        risk_by_label[
            label
        ] = float(
            proba_list[i][0][1]
        )

    # ------------------------------------------------------------
    # Optional laboratory boost
    # ------------------------------------------------------------

    risk_by_label = apply_lab_boost(
        db,
        user_id,
        risk_by_label,
    )

    # ------------------------------------------------------------
    # Build risk items
    # ------------------------------------------------------------

    risk_items = []
    score_probabilities = []

    for label in label_order:

        probability = (
            risk_by_label[label]
        )

        score_probabilities.append(
            probability
        )

        nutrient_col = (
            LABEL_TO_NUTRIENT_COL[
                label
            ]
        )

        diary_avg = (
            diary[
                "averages"
            ].get(
                nutrient_col
            )
        )

        low_intake_tag = None

        if (
            diary_avg is not None
            and nutrient_col
            in RDA_THRESHOLDS
            and diary_avg
            < RDA_THRESHOLDS[
                nutrient_col
            ]
        ):

            nutrient_name = (
                label
                .replace(
                    "label_",
                    "",
                )
                .replace(
                    "_",
                    " ",
                )
            )

            low_intake_tag = (
                f"Low {nutrient_name} intake"
            )

        risk_items.append(
            {
                "label": label,
                "nutrient": (
                    label
                    .replace(
                        "label_",
                        "",
                    )
                ),
                "probability": round(
                    probability,
                    3,
                ),
                "predicted_deficient": (
                    probability >= 0.5
                ),
                "ui_percent": round(
                    probability * 100
                ),
                "ui_level": ui_level(
                    probability
                ),
                "tag": low_intake_tag,
            }
        )

    # ------------------------------------------------------------
    # Wellness score
    # ------------------------------------------------------------

    overall_score = (
        calculate_wellness_score(
            score_probabilities
        )
    )

    # ------------------------------------------------------------
    # Recommendations
    #
    # This happens AFTER ML prediction and does not
    # affect the model or wellness score.
    # ------------------------------------------------------------

    recommendations = (
        build_recommendations(
            db,
            user_id,
            risk_items,
        )
    )

    return {
        "features": feature_dict,
        "risks": risk_items,
        "overall_score": overall_score,
        "diary_days_used": diary[
            "distinct_days"
        ],
        "recommendations": recommendations,
    }