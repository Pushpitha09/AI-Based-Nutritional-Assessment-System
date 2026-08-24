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


# ============================================================
# PATHS
# ============================================================

ARTIFACTS_DIR = (
    Path(__file__).parent.parent
    / "ml_artifacts"
)


# ============================================================
# ASSESSMENT SETTINGS
# ============================================================

MIN_DIARY_DAYS = 3

DEFAULT_WINDOW_DAYS = 7

REQUIRED_MEALS = {
    "breakfast",
    "lunch",
    "snack",
    "dinner",
}


# ============================================================
# DIARY NUTRIENT COLUMNS
# ============================================================

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


# ============================================================
# UI INTAKE THRESHOLDS
#
# These values are ONLY used for the "Low X intake" tag.
# They are NOT used by the ML model.
# ============================================================

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


# ============================================================
# MODEL LABEL -> DATABASE NUTRIENT COLUMN
# ============================================================

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


# ============================================================
# RECOMMENDATION SETTINGS
# ============================================================

RECOMMENDATION_THRESHOLD = 0.45

RECOMMENDATIONS_PER_NUTRIENT = 6


# ============================================================
# DATA SOURCE PRIORITY
#
# Used only as a tie-breaker for food recommendations.
# Does NOT affect assessment.
# ============================================================

SOURCE_PRIORITY = {
    "seed": 0,
    "ifct": 1,
    "usda": 2,
    "usda_sr_legacy": 2,
}


# ============================================================
# UNSUITABLE FOOD TERMS
#
# These foods should not normally appear as recommendations.
# ============================================================

UNSUITABLE_RECOMMENDATION_TERMS = (

    # Raw foods
    ", raw",
    " raw",

    # Organs
    "liver",
    "kidney",
    "giblet",
    "gizzard",
    "heart",
    "tongue",
    "tripe",
    "brain",

    # Liver products
    "liverwurst",
    "liver sausage",
    "braunschweiger",
    "liver cheese",
    "pate",

    # Powders / mixes
    "powder",
    "dry mix",
    "unprepared",
    "not reconstituted",

    # Spices / herbs
    "spices,",
    "paprika",
    "marjoram",
    "spearmint",
    "chives",

    # Additives
    "baking powder",
    "leavening agent",
    "salt substitute",
    "food additive",
    "food coloring",
    "food colouring",
    "flavoring",
    "flavouring",
    "yeast extract",

    # Infant foods
    "babyfood",
    "baby food",
    "infant formula",
    "toddler",

    # Processed / unusual foods
    "candies",
    "pie",
    "puddings",
    "salad dressing",
    "refrigerated dough",

    # Supplements
    "tablet",
    "supplement",

    # Other unsuitable entries
    "food distribution program",
    "artificial flavor",
    "artificial flavour",
    "whey, acid",
    "margarine",

    # Unusual animal foods
    "seal",
    "whale",
)


def _is_unsuitable_recommendation_food(
    name: str,
) -> bool:
    """
    Returns True when a food should not be shown
    as a normal meal recommendation.
    """

    name_lower = name.casefold()

    return any(
        term in name_lower
        for term in UNSUITABLE_RECOMMENDATION_TERMS
    )


# ============================================================
# FOOD CATEGORY PREFERENCE
#
# Gives practical everyday foods a bonus.
# This does NOT change ML assessment.
# ============================================================

def _food_category_score(
    name: str,
) -> int:

    name_lower = name.casefold()

    scores = {

        # Everyday practical foods
        5: (
            "milk",
            "curd",
            "yogurt",
            "yoghurt",
            "paneer",
            "tofu",
            "egg",
            "spinach",
            "broccoli",
            "carrot",
            "tomato",
            "orange",
            "guava",
            "papaya",
            "mango",
            "banana",
            "apple",
            "lentil",
            "dal",
            "chickpea",
            "chana",
            "bean",
            "peas",
            "ragi",
            "finger millet",
            "sesame",
            "almond",
            "cashew",
            "walnut",
            "flaxseed",
            "chia",
            "pumpkin seed",
        ),

        # Common nutritious foods
        4: (
            "cheese",
            "chicken",
            "salmon",
            "tuna",
            "sardine",
            "mackerel",
            "trout",
            "soy",
            "soybean",
            "oats",
            "brown rice",
            "sweet potato",
            "capsicum",
            "drumstick",
            "agathi",
            "fortified cereal",
            "breakfast cereal",
        ),

        # Valid but less common
        3: (
            "beef",
            "lamb",
            "pork",
            "clam",
            "mollusk",
            "oyster",
            "mussel",
            "shrimp",
            "prawn",
            "crab",
        ),
    }

    for score in sorted(
        scores.keys(),
        reverse=True,
    ):

        if any(
            keyword in name_lower
            for keyword in scores[score]
        ):
            return score

    return 2


# ============================================================
# NUTRIENT SCORE
#
# Converts nutrient value into a capped score.
#
# This is ONLY for recommendation ranking.
# ============================================================

def _nutrient_score(
    value: float,
    nutrient_col: str,
) -> float:

    reference_values = {

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

    reference = reference_values.get(
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


# ============================================================
# RECOMMENDATION SCORE
# ============================================================

def _recommendation_score(
    food,
    nutrient_col: str,
) -> tuple:

    value = float(
        getattr(
            food,
            nutrient_col,
        )
        or 0
    )

    category_score = (
        _food_category_score(
            food.name
        )
    )

    nutrient_score = (
        _nutrient_score(
            value,
            nutrient_col,
        )
    )

    quality_score = (
        food_quality_score(
            food.name
        )
    )

    source_score = (
        SOURCE_PRIORITY.get(
            food.source,
            3,
        )
    )

    return (
        category_score,
        quality_score,
        nutrient_score,
        -source_score,
        food.name.lower(),
    )


# ============================================================
# RECOMMENDED FOODS
# ============================================================

def get_recommended_foods(
    db: Session,
    profile: HealthProfile,
    nutrient_col: str,
    limit: int = RECOMMENDATIONS_PER_NUTRIENT,
):

    restrictions = []

    if (
        profile
        and profile.dietary_restrictions
    ):

        restrictions = (
            normalize_restrictions(
                profile.dietary_restrictions.split(",")
            )
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

    # --------------------------------------------------------
    # FILTER FOODS
    # --------------------------------------------------------

    candidates = [

        food

        for food in candidates

        if is_good_recommendation_food(
            food.name
        )

        and not _is_unsuitable_recommendation_food(
            food.name
        )

        and food_matches_restrictions(
            food,
            restrictions,
        )

    ]

    # --------------------------------------------------------
    # SORT FOODS
    # --------------------------------------------------------

    candidates.sort(

        key=lambda food: (
            _recommendation_score(
                food,
                nutrient_col,
            )
        ),

        reverse=True,
    )

    results = []

    seen_foods = set()

    # --------------------------------------------------------
    # BUILD FINAL RESULTS
    # --------------------------------------------------------

    for food in candidates:

        food_key = get_food_key(
            food.name
        )

        if food_key in seen_foods:
            continue

        seen_foods.add(
            food_key
        )

        amount = float(
            getattr(
                food,
                nutrient_col,
            )
            or 0
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

        if len(results) >= limit:
            break

    return results


# ============================================================
# BUILD RECOMMENDATIONS
# ============================================================

def build_recommendations(
    db: Session,
    user_id: int,
    risk_items: list,
) -> dict:

    profile = (
        db.query(
            HealthProfile
        )
        .filter(
            HealthProfile.user_id
            == user_id
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

        key=lambda risk: (
            risk["probability"]
        ),

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


# ============================================================
# CUSTOM ERROR
# ============================================================

class AssessmentError(
    Exception
):
    pass


# ============================================================
# LOAD ML ARTIFACTS
# ============================================================

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

                "preprocess.joblib, and meta.json in "

                "backend/app/ml_artifacts/"
            )

    model = joblib.load(
        model_path
    )

    preprocess = joblib.load(
        preprocess_path
    )

    with open(
        meta_path
    ) as file:

        meta = json.load(
            file
        )

    return (
        model,
        preprocess,
        meta,
    )


# ============================================================
# DIARY SUMMARY
# ============================================================

def get_diary_summary(
    db: Session,
    user_id: int,
    window_days: int = DEFAULT_WINDOW_DAYS,
) -> dict:

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

            DiaryEntry.user_id
            == user_id,

            DiaryEntry.entry_date
            >= since,
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

    # --------------------------------------------------------
    # ONLY COMPLETE DAYS
    # --------------------------------------------------------

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

    if (
        distinct_days
        < MIN_DIARY_DAYS
    ):

        raise AssessmentError(

            f"Need at least {MIN_DIARY_DAYS} "

            "days with breakfast, lunch, snack, "

            f"and dinner logged in the last "

            f"{window_days} days "

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

        for col in (
            DIARY_NUTRIENT_COLS
        ):

            averages[col] += (
                day_totals[col]
            )

    for col in (
        DIARY_NUTRIENT_COLS
    ):

        averages[col] = (
            averages[col]
            / distinct_days
        )

    return {

        "averages": averages,

        "distinct_days": distinct_days,
    }


# ============================================================
# BUILD MODEL FEATURES
# ============================================================

def build_feature_dict(
    db: Session,
    user_id: int,
    diary_averages: dict,
) -> dict:

    profile = (

        db.query(
            HealthProfile
        )

        .filter(
            HealthProfile.user_id
            == user_id
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


# ============================================================
# LAB BOOST
# ============================================================

def apply_lab_boost(
    db: Session,
    user_id: int,
    risk_by_label: dict,
) -> dict:

    labs = (

        db.query(
            LabResult
        )

        .filter(
            LabResult.user_id
            == user_id
        )

        .first()
    )

    if not labs:
        return risk_by_label

    profile = (

        db.query(
            HealthProfile
        )

        .filter(
            HealthProfile.user_id
            == user_id
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

    # Iron / Hemoglobin

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

            boosted["label_iron"] = max(

                boosted.get(
                    "label_iron",
                    0,
                ),

                0.75,
            )

    if (

        labs.ferritin
        is not None

        and labs.ferritin < 30

    ):

        boosted["label_iron"] = max(

            boosted.get(
                "label_iron",
                0,
            ),

            0.70,
        )

    # Vitamin D

    if (

        labs.serum_vitamin_d
        is not None

        and labs.serum_vitamin_d < 50

    ):

        boosted["label_vitamin_d"] = max(

            boosted.get(
                "label_vitamin_d",
                0,
            ),

            0.65,
        )

    # Vitamin B12

    if (

        labs.vitamin_b12
        is not None

        and labs.vitamin_b12 < 200

    ):

        boosted["label_vitamin_b12"] = max(

            boosted.get(
                "label_vitamin_b12",
                0,
            ),

            0.60,
        )

    # Calcium

    if (

        labs.calcium
        is not None

        and labs.calcium < 8.5

    ):

        boosted["label_calcium"] = max(

            boosted.get(
                "label_calcium",
                0,
            ),

            0.55,
        )

    return boosted


# ============================================================
# UI RISK LEVEL
# ============================================================

def ui_level(
    probability: float,
) -> str:

    if probability > 0.65:
        return "HIGH"

    if probability >= 0.35:
        return "MODERATE"

    return "LOW"


# ============================================================
# WELLNESS SCORE
# ============================================================

def calculate_wellness_score(
    probabilities: list[float],
) -> float:

    if not probabilities:

        raise ValueError(
            "At least one deficiency probability "
            "is required"
        )

    average_risk = (

        sum(
            probabilities
        )

        / len(
            probabilities
        )
    )

    return round(
        (
            1 - average_risk
        ) * 100,
        1,
    )


# ============================================================
# RUN ASSESSMENT
# ============================================================

def run_assessment(
    db: Session,
    user_id: int,
    window_days: int = DEFAULT_WINDOW_DAYS,
) -> dict:

    # --------------------------------------------------------
    # LOAD MODEL
    # --------------------------------------------------------

    (
        model,
        preprocess,
        meta,
    ) = _load_artifacts()

    feature_order = (
        meta["features"]
    )

    label_order = (
        meta["labels"]
    )

    # --------------------------------------------------------
    # GET DIARY DATA
    # --------------------------------------------------------

    diary = get_diary_summary(

        db,

        user_id,

        window_days,
    )

    # --------------------------------------------------------
    # BUILD FEATURES
    # --------------------------------------------------------

    feature_dict = (
        build_feature_dict(

            db,

            user_id,

            diary["averages"],
        )
    )

    X = pd.DataFrame(
        [feature_dict]
    )[feature_order]

    # --------------------------------------------------------
    # PREPROCESS
    # --------------------------------------------------------

    X_processed = (
        preprocess.transform(
            X
        )
    )

    # --------------------------------------------------------
    # RANDOM FOREST PREDICTION
    # --------------------------------------------------------

    proba_list = (
        model.predict_proba(
            X_processed
        )
    )

    risk_by_label = {}

    for i, label in enumerate(
        label_order
    ):

        risk_by_label[label] = float(

            proba_list[i][0][1]
        )

    # --------------------------------------------------------
    # OPTIONAL LAB BOOST
    # --------------------------------------------------------

    risk_by_label = (
        apply_lab_boost(

            db,

            user_id,

            risk_by_label,
        )
    )

    # --------------------------------------------------------
    # BUILD RISK RESULTS
    # --------------------------------------------------------

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
            diary["averages"].get(
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

    # --------------------------------------------------------
    # WELLNESS SCORE
    # --------------------------------------------------------

    overall_score = (
        calculate_wellness_score(
            score_probabilities
        )
    )

    # --------------------------------------------------------
    # FOOD RECOMMENDATIONS
    #
    # This happens AFTER the ML prediction.
    # It does not change the prediction.
    # --------------------------------------------------------

    recommendations = (
        build_recommendations(

            db,

            user_id,

            risk_items,
        )
    )

    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    return {

        "features": feature_dict,

        "risks": risk_items,

        "overall_score": overall_score,

        "diary_days_used": (
            diary["distinct_days"]
        ),

        "recommendations": recommendations,
    }