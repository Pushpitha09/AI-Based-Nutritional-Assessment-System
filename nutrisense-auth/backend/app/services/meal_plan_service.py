
import json
import re

from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.food_item import FoodItem
from app.models.health_profile import HealthProfile
from app.models.meal_plan import MealPlan

from app.services.food_tags import (
    food_matches_restrictions,
    normalize_restrictions,
    is_good_recommendation_food,
    food_quality_score,
)


# ============================================================
# MEAL PLAN SETTINGS
# ============================================================

MEALS = (
    "breakfast",
    "lunch",
    "snack",
    "dinner",
)

DAYS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)

FOCUS_LIMIT = 4
FOODS_PER_MEAL = 2


# ============================================================
# NUTRIENT NORMALIZATION TARGETS
# ============================================================

# These values are used ONLY for recommendation ranking.
# They do NOT affect:
#
# - Random Forest model
# - ML training
# - assessment probabilities
# - deficiency prediction
# - wellness score

NUTRIENT_TARGETS = {
    "iron": 18.0,
    "calcium": 1000.0,
    "magnesium": 320.0,
    "zinc": 8.0,
    "vitamin_d": 15.0,
    "vitamin_b12": 2.4,
    "folate": 400.0,
    "vitamin_a": 700.0,
    "vitamin_c": 75.0,
    "protein": 50.0,
}


# ============================================================
# FOOD NAME HELPERS
# ============================================================

def _food_family(name: str) -> str:
    """
    Create a simplified food family name.

    This helps prevent the same food from appearing repeatedly
    on the same day.
    """

    primary = name.split(",", 1)[0].strip().casefold()

    return re.sub(
        r"[^a-z0-9]+",
        " ",
        primary,
    ).strip()


def _display_food_name(name: str) -> str:
    """
    Clean unnecessary catalog metadata from food names.
    """

    cleaned = re.sub(
        r"\([^)]*food distribution program[^)]*\)",
        "",
        name,
        flags=re.IGNORECASE,
    )

    ignored_segments = {
        "imported",
        "new zealand",
        "variety meats and by-products",
        "by-products",
    }

    segments = []

    for segment in cleaned.split(","):

        segment = re.sub(
            r"\s{2,}",
            " ",
            segment,
        ).strip()

        if (
            segment
            and segment.casefold()
            not in ignored_segments
        ):
            segments.append(segment)

    return ", ".join(segments)


# ============================================================
# FOOD SUITABILITY FILTERING
# ============================================================

def _is_suitable_meal_food(food) -> bool:
    """
    Check whether a food is suitable to show in a normal meal plan.

    This removes:
    - raw foods
    - raw meat
    - organs
    - giblets
    - liver
    - powders
    - spices
    - dry mixes
    - infant foods
    - highly unsuitable catalog items
    """

    name = (food.name or "").lower()

    # Use the general recommendation quality filter first.
    if not is_good_recommendation_food(food.name):
        return False

    unsuitable_terms = [

        # Raw / uncooked foods
        " raw",
        ",raw",

        # Organ meats
        "liver",
        "kidney",
        "gizzard",
        "heart",
        "tongue",
        "tripe",
        "brain",

        # Giblets / by-products
        "giblet",
        "variety meat",
        "by-product",

        # Processed organ products
        "liverwurst",
        "braunschweiger",
        "liver sausage",
        "liver cheese",
        "pate",

        # Powders and mixes
        "powder",
        "dry mix",
        "unprepared",
        "not reconstituted",
        "mix,",

        # Spices and herbs
        "spices,",
        "paprika",
        "marjoram",
        "spearmint",
        "chives",

        # Infant foods
        "infant",
        "babyfood",
        "baby food",
        "toddler",

        # Strange animal foods
        "seal",
        "whale",

        # Ingredients that should not be meals
        "baking powder",
        "leavening",
        "table salt",
        "salt substitute",
        "seasoning",
        "flavoring",
        "flavouring",
        "food coloring",
        "food colouring",
        "extract",
        "yeast extract",

        # Other unsuitable items
        "margarine",
        "whey, acid",
    ]

    if any(
        term in name
        for term in unsuitable_terms
    ):
        return False

    return True


# ============================================================
# DIETARY RESTRICTION FILTERING
# ============================================================

def _matches_restrictions(food, restrictions):
    """
    Check whether a FoodItem matches the user's dietary restrictions.
    """

    return food_matches_restrictions(
        food,
        restrictions,
    )


# ============================================================
# NUTRIENT HELPERS
# ============================================================

def _get_nutrient_column(nutrient: str) -> str:
    """
    Map nutrient names to FoodItem database columns.
    """

    mapping = {
        "iron": "iron_mg",
        "calcium": "calcium_mg",
        "magnesium": "magnesium_mg",
        "zinc": "zinc_mg",
        "vitamin_d": "vitamin_d_mcg",
        "vitamin_b12": "vitamin_b12_mcg",
        "folate": "folate_mcg",
        "vitamin_a": "vitamin_a_mcg",
        "vitamin_c": "vitamin_c_mg",
        "protein": "protein_g",
    }

    return mapping.get(nutrient)


def get_normalized_nutrient_score(
    food,
    nutrients,
) -> float:
    """
    Calculate a normalized nutrient score.

    Different nutrients use different units and ranges.

    For example:

    Calcium:
        1000 mg target

    Vitamin B12:
        2.4 mcg target

    Without normalization, raw values can cause one nutrient
    to dominate recommendations.

    This function compares each nutrient value against its
    reference target.

    IMPORTANT:
    This function is ONLY used for food recommendation ranking.
    It does NOT affect the ML assessment model.
    """

    score = 0.0

    for nutrient in nutrients:

        target = NUTRIENT_TARGETS.get(nutrient)

        column = _get_nutrient_column(nutrient)

        if not target or not column:
            continue

        value = float(
            getattr(
                food,
                column,
                0,
            )
            or 0
        )

        # Ignore invalid negative values.
        value = max(
            value,
            0,
        )

        normalized_value = value / target

        # Prevent a single extremely large value from
        # completely dominating the recommendation.
        normalized_value = min(
            normalized_value,
            2.0,
        )

        score += normalized_value

    return score


def _meal_food_score(
    food,
    focus_nutrients,
) -> float:
    """
    Combine nutrient contribution with a small preference
    for recognizable, normal foods.

    Nutrient score remains the main factor.
    """

    nutrient_score = get_normalized_nutrient_score(
        food,
        focus_nutrients,
    )

    quality_bonus = food_quality_score(
        food.name,
    ) * 0.05

    return nutrient_score + quality_bonus


# ============================================================
# ASSESSMENT FOCUS NUTRIENTS
# ============================================================

def _focus_nutrients(assessment):
    """
    Get the highest-risk nutrients from the latest assessment.
    """

    risks = json.loads(
        assessment.risks_json
    )

    focused = [
        risk
        for risk in risks
        if risk["probability"] >= 0.45
    ]

    focused.sort(
        key=lambda risk: risk["probability"],
        reverse=True,
    )

    if focused:

        return [
            risk["nutrient"]
            for risk in focused[:FOCUS_LIMIT]
        ]

    sorted_risks = sorted(
        risks,
        key=lambda risk: risk["probability"],
        reverse=True,
    )

    return [
        risk["nutrient"]
        for risk in sorted_risks[:FOCUS_LIMIT]
    ]


# ============================================================
# SAVED PLAN VALIDATION
# ============================================================

def _saved_plan_is_valid(
    plan,
    restrictions,
) -> bool:
    """
    Check whether an existing meal plan is still valid.

    The saved plan is regenerated when:

    - dietary restrictions changed
    - an unsuitable food exists
    - a food no longer matches restrictions
    """

    for day in plan:

        for meal in day.get(
            "meals",
            [],
        ):

            for food_data in meal.get(
                "foods",
                [],
            ):

                source_name = food_data.get(
                    "source_name",
                    food_data.get(
                        "name",
                        "",
                    ),
                )

                temp_food = type(
                    "TempFood",
                    (),
                    {
                        "name": source_name,
                    },
                )()

                if not _matches_restrictions(
                    temp_food,
                    restrictions,
                ):
                    return False

                if not _is_suitable_meal_food(
                    temp_food
                ):
                    return False

    return True


# ============================================================
# CANDIDATE FOOD COLLECTION
# ============================================================

def _get_candidate_foods(
    db,
    restrictions,
):
    """
    Get foods that:

    1. Match dietary restrictions
    2. Are suitable normal meal foods
    """

    all_foods = db.query(
        FoodItem
    ).all()

    candidates = []

    for food in all_foods:

        if not _matches_restrictions(
            food,
            restrictions,
        ):
            continue

        if not _is_suitable_meal_food(
            food
        ):
            continue

        candidates.append(
            food
        )

    return candidates


# ============================================================
# MEAL PLAN GENERATION
# ============================================================

def generate_meal_plan(
    db: Session,
    user_id: int,
) -> dict:

    # --------------------------------------------------------
    # Get latest assessment
    # --------------------------------------------------------

    assessment = (
        db.query(Assessment)
        .filter(
            Assessment.user_id == user_id
        )
        .order_by(
            Assessment.created_at.desc()
        )
        .first()
    )

    if not assessment:

        raise ValueError(
            "Run an assessment before generating a meal plan."
        )

    # --------------------------------------------------------
    # Get user dietary restrictions
    # --------------------------------------------------------

    profile = (
        db.query(HealthProfile)
        .filter(
            HealthProfile.user_id == user_id
        )
        .first()
    )

    restrictions = []

    if (
        profile
        and profile.dietary_restrictions
    ):

        restrictions = normalize_restrictions(
            profile.dietary_restrictions.split(
                ","
            )
        )

    # --------------------------------------------------------
    # Get focus nutrients from assessment
    # --------------------------------------------------------

    focus_nutrients = _focus_nutrients(
        assessment
    )

    # --------------------------------------------------------
    # Get suitable foods
    # --------------------------------------------------------

    candidates = _get_candidate_foods(
        db,
        restrictions,
    )

    if len(candidates) < FOODS_PER_MEAL:

        raise ValueError(
            "Not enough suitable foods match your dietary "
            "restrictions to build a meal plan."
        )

    # --------------------------------------------------------
    # Rank foods using NORMALIZED nutrient scoring
    # --------------------------------------------------------

    ranked = sorted(
        candidates,
        key=lambda food: _meal_food_score(
            food,
            focus_nutrients,
        ),
        reverse=True,
    )

    # Keep a reasonably large pool for variety.
    pool_size = min(
        len(ranked),
        max(
            80,
            FOODS_PER_MEAL
            * len(MEALS)
            * 7,
        ),
    )

    pool = ranked[:pool_size]

    # --------------------------------------------------------
    # Build seven-day meal plan
    # --------------------------------------------------------

    plan = []

    for day_index, day in enumerate(DAYS):

        used_today = set()

        used_families = set()

        meals = []

        for meal_index, meal in enumerate(MEALS):

            foods = []

            start = (
                day_index * 7
                + meal_index * 5
            ) % len(pool)

            ordered_pool = (
                pool[start:]
                + pool[:start]
            )

            # First pass:
            # avoid duplicate food families on the same day.

            for food in ordered_pool:

                family = _food_family(
                    food.name
                )

                if food.id in used_today:
                    continue

                if family in used_families:
                    continue

                foods.append(
                    {
                        "id": food.id,
                        "name": _display_food_name(
                            food.name
                        ),
                        "source_name": food.name,
                        "portion_grams": 100,
                    }
                )

                used_today.add(
                    food.id
                )

                used_families.add(
                    family
                )

                if len(foods) == FOODS_PER_MEAL:
                    break

            # Second pass:
            # If not enough foods are available, allow another
            # family variant but still never repeat the same ID.

            if len(foods) < FOODS_PER_MEAL:

                for food in ordered_pool:

                    if food.id in used_today:
                        continue

                    foods.append(
                        {
                            "id": food.id,
                            "name": _display_food_name(
                                food.name
                            ),
                            "source_name": food.name,
                            "portion_grams": 100,
                        }
                    )

                    used_today.add(
                        food.id
                    )

                    if len(foods) == FOODS_PER_MEAL:
                        break

            meals.append(
                {
                    "meal": meal,
                    "foods": foods,
                }
            )

        plan.append(
            {
                "day": day,
                "meals": meals,
            }
        )

    # --------------------------------------------------------
    # Replace old meal plan
    # --------------------------------------------------------

    db.query(MealPlan).filter(
        MealPlan.user_id == user_id
    ).delete(
        synchronize_session=False
    )

    record = MealPlan(
        user_id=user_id,
        assessment_id=assessment.id,
        dietary_restrictions=", ".join(
            restrictions
        ),
        plan_json=json.dumps(
            plan
        ),
    )

    db.add(
        record
    )

    db.commit()

    db.refresh(
        record
    )

    # --------------------------------------------------------
    # Return meal plan
    # --------------------------------------------------------

    return {
        "id": record.id,
        "assessment_id": assessment.id,
        "dietary_restrictions": restrictions,
        "focus_nutrients": focus_nutrients,
        "created_at": record.created_at,
        "days": plan,
    }


# ============================================================
# GET LATEST MEAL PLAN
# ============================================================

def get_latest_meal_plan(
    db: Session,
    user_id: int,
):

    record = (
        db.query(MealPlan)
        .filter(
            MealPlan.user_id == user_id
        )
        .order_by(
            MealPlan.created_at.desc()
        )
        .first()
    )

    if not record:

        return None

    # --------------------------------------------------------
    # Get current dietary restrictions
    # --------------------------------------------------------

    profile = (
        db.query(HealthProfile)
        .filter(
            HealthProfile.user_id == user_id
        )
        .first()
    )

    current_restrictions = []

    if (
        profile
        and profile.dietary_restrictions
    ):

        current_restrictions = normalize_restrictions(
            profile.dietary_restrictions.split(
                ","
            )
        )

    saved_restrictions = normalize_restrictions(
        record.dietary_restrictions.split(
            ","
        )
    )

    saved_plan = json.loads(
        record.plan_json
    )

    # --------------------------------------------------------
    # Regenerate if restrictions changed or old plan contains
    # unsuitable foods.
    # --------------------------------------------------------

    if (
        saved_restrictions
        != current_restrictions
        or not _saved_plan_is_valid(
            saved_plan,
            current_restrictions,
        )
    ):

        return generate_meal_plan(
            db,
            user_id,
        )

    # --------------------------------------------------------
    # Get assessment for focus nutrients
    # --------------------------------------------------------

    assessment = (
        db.query(Assessment)
        .filter(
            Assessment.id
            == record.assessment_id
        )
        .first()
    )

    return {
        "id": record.id,
        "assessment_id": record.assessment_id,
        "dietary_restrictions": [
            item.strip()
            for item in record.dietary_restrictions.split(
                ","
            )
            if item.strip()
        ],
        "focus_nutrients": _focus_nutrients(
            assessment
        ),
        "created_at": record.created_at,
        "days": saved_plan,
    }
