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


# -------------------------------------------------------------------
# Meal category preferences
# -------------------------------------------------------------------

MEAL_KEYWORDS = {

    "breakfast": (
        "oat",
        "oatmeal",
        "ragi",
        "finger millet",
        "cereal",
        "poha",
        "flattened rice",
        "idli",
        "dosa",
        "upma",
        "bread",
        "roti",
        "chapati",
        "atta",
        "banana",
        "apple",
        "papaya",
        "orange",
        "guava",
        "milk",
        "soymilk",
        "soy milk",
        "curd",
        "yogurt",
        "yoghurt",
        "egg",
        "tofu",
    ),

    "lunch": (
        "rice",
        "brown rice",
        "roti",
        "chapati",
        "wheat",
        "atta",
        "lentil",
        "dal",
        "chickpea",
        "chana",
        "rajma",
        "kidney bean",
        "bean",
        "peas",
        "green gram",
        "moong",
        "tofu",
        "soybean",
        "spinach",
        "amaranth",
        "carrot",
        "tomato",
        "capsicum",
        "broccoli",
        "vegetable",
    ),

    "snack": (
        "banana",
        "apple",
        "orange",
        "guava",
        "papaya",
        "mango",
        "fruit",
        "almond",
        "cashew",
        "walnut",
        "sesame",
        "pumpkin seed",
        "chia",
        "flaxseed",
        "chickpea",
        "chana",
        "roasted",
        "curd",
        "yogurt",
        "yoghurt",
        "soymilk",
        "soy milk",
        "milk",
        "oat",
    ),

    "dinner": (
        "rice",
        "brown rice",
        "roti",
        "chapati",
        "wheat",
        "atta",
        "lentil",
        "dal",
        "chickpea",
        "chana",
        "rajma",
        "kidney bean",
        "bean",
        "peas",
        "green gram",
        "moong",
        "tofu",
        "soybean",
        "spinach",
        "amaranth",
        "carrot",
        "tomato",
        "capsicum",
        "broccoli",
        "vegetable",
    ),
}


UNSUITABLE_MEAL_TERMS = (
    " raw",
    ",raw",
    "raw,",
    "liver",
    "kidney",
    "gizzard",
    "heart",
    "tongue",
    "tripe",
    "brain",
    "giblet",
    "variety meat",
    "by-product",
    "liverwurst",
    "braunschweiger",
    "liver sausage",
    "liver cheese",
    "pate",
    "powder",
    "dry mix",
    "unprepared",
    "not reconstituted",
    "mix,",
    "spices,",
    "paprika",
    "marjoram",
    "spearmint",
    "chives",
    "infant",
    "babyfood",
    "baby food",
    "toddler",
    "seal",
    "whale",
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
    "margarine",
    "whey, acid",
    "caramel-coated",
    "confection",
    "heavy syrup",
    "syrup, solids",
    "salad dressing",
    "pie",
    "pudding",
    "candy",
    "candies",
)


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _food_family(name):

    primary = (
        name
        .split(",", 1)[0]
        .strip()
        .casefold()
    )

    return re.sub(
        r"[^a-z0-9]+",
        " ",
        primary,
    ).strip()


def _display_food_name(name):

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


def _keyword_match(name, keywords):

    text = (name or "").casefold()

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


def _is_suitable_meal_food(food):

    name = (
        food.name or ""
    ).casefold()

    if not is_good_recommendation_food(
        food.name
    ):
        return False

    if any(
        term in name
        for term in UNSUITABLE_MEAL_TERMS
    ):
        return False

    return True


def _matches_restrictions(
    food,
    restrictions,
):

    return food_matches_restrictions(
        food,
        restrictions,
    )


def _get_nutrient_column(nutrient):

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


# Same IFCT handling as recommendation service.
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


def _nutrient_value(
    food,
    column,
):

    value = float(
        getattr(
            food,
            column,
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
        and column
        in IFCT_MICRONUTRIENT_COLUMNS
    ):
        value *= 1000

    return value


def get_normalized_nutrient_score(
    food,
    nutrients,
):

    score = 0.0

    for nutrient in nutrients:

        target = NUTRIENT_TARGETS.get(
            nutrient
        )

        column = _get_nutrient_column(
            nutrient
        )

        if (
            not target
            or not column
        ):
            continue

        value = _nutrient_value(
            food,
            column,
        )

        normalized_value = (
            value / target
        )

        # Don't allow one unusually large
        # database value to dominate everything.
        normalized_value = min(
            normalized_value,
            1.0,
        )

        score += normalized_value

    return score


def _meal_food_score(
    food,
    meal,
    focus_nutrients,
):

    category_score = _keyword_match(
        food.name,
        MEAL_KEYWORDS[meal],
    )

    nutrient_score = (
        get_normalized_nutrient_score(
            food,
            focus_nutrients,
        )
    )

    quality_bonus = (
        food_quality_score(
            food.name
        )
        * 0.05
    )

    return (
        category_score * 3
        + nutrient_score
        + quality_bonus
    )


def _focus_nutrients(
    assessment,
):

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
            for risk in focused[
                :FOCUS_LIMIT
            ]
        ]

    sorted_risks = sorted(
        risks,
        key=lambda risk: risk["probability"],
        reverse=True,
    )

    return [
        risk["nutrient"]
        for risk in sorted_risks[
            :FOCUS_LIMIT
        ]
    ]


def _saved_plan_is_valid(
    plan,
    restrictions,
):

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
                        "name": source_name
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


def _get_candidate_foods(
    db,
    restrictions,
):

    all_foods = (
        db.query(FoodItem)
        .all()
    )

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

        candidates.append(food)

    return candidates


# -------------------------------------------------------------------
# Meal plan generation
# -------------------------------------------------------------------

def generate_meal_plan(
    db,
    user_id,
):

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

    focus_nutrients = _focus_nutrients(
        assessment
    )

    candidates = _get_candidate_foods(
        db,
        restrictions,
    )

    if len(candidates) < FOODS_PER_MEAL:

        raise ValueError(
            "Not enough suitable foods match your dietary restrictions "
            "to build a meal plan."
        )

    # ---------------------------------------------------------------
    # Rank foods separately for each meal.
    # ---------------------------------------------------------------

    meal_rankings = {}

    for meal in MEALS:

        meal_rankings[meal] = sorted(
            candidates,
            key=lambda food: _meal_food_score(
                food,
                meal,
                focus_nutrients,
            ),
            reverse=True,
        )

    plan = []

    # Foods/families used recently.
    # This helps prevent the same food appearing every day.
    recent_families = []

    for day_index, day in enumerate(DAYS):

        used_today = set()
        used_families_today = set()

        meals = []

        for meal_index, meal in enumerate(MEALS):

            ranked = meal_rankings[meal]

            foods = []

            # Deterministic rotation through the ranked list.
            start = (
                day_index * 5
                + meal_index * 7
            ) % max(
                len(ranked),
                1,
            )

            ordered = (
                ranked[start:]
                + ranked[:start]
            )

            # -------------------------------------------------------
            # First pass:
            # category match + no recent repetition
            # -------------------------------------------------------

            for food in ordered:

                family = _food_family(
                    food.name
                )

                if food.id in used_today:
                    continue

                if family in used_families_today:
                    continue

                # Don't use the same family too frequently.
                if family in recent_families:
                    continue

                category_match = _keyword_match(
                    food.name,
                    MEAL_KEYWORDS[meal],
                )

                if category_match == 0:
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

                used_families_today.add(
                    family
                )

                recent_families.append(
                    family
                )

                if len(
                    recent_families
                ) > 12:

                    recent_families.pop(
                        0
                    )

                if len(foods) == FOODS_PER_MEAL:
                    break

            # -------------------------------------------------------
            # Second pass:
            # allow foods used recently if necessary
            # -------------------------------------------------------

            if len(foods) < FOODS_PER_MEAL:

                for food in ordered:

                    family = _food_family(
                        food.name
                    )

                    if food.id in used_today:
                        continue

                    if family in used_families_today:
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

                    used_families_today.add(
                        family
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

    # ---------------------------------------------------------------
    # Save latest plan
    # ---------------------------------------------------------------

    (
        db.query(MealPlan)
        .filter(
            MealPlan.user_id == user_id
        )
        .delete(
            synchronize_session=False
        )
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

    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "id": record.id,
        "assessment_id": record.assessment_id,
        "dietary_restrictions": restrictions,
        "focus_nutrients": focus_nutrients,
        "created_at": record.created_at,
        "days": plan,
    }


# -------------------------------------------------------------------
# Get latest plan
# -------------------------------------------------------------------

def get_latest_meal_plan(
    db,
    user_id,
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

        current_restrictions = (
            normalize_restrictions(
                profile.dietary_restrictions.split(
                    ","
                )
            )
        )

    saved_restrictions = (
        normalize_restrictions(
            record.dietary_restrictions.split(
                ","
            )
        )
    )

    saved_plan = json.loads(
        record.plan_json
    )

    # Regenerate automatically if the user's
    # dietary preferences have changed or
    # the saved plan contains an unsuitable food.
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
            for item
            in record.dietary_restrictions.split(
                ","
            )
            if item.strip()
        ],
        "focus_nutrients": (
            _focus_nutrients(
                assessment
            )
            if assessment
            else []
        ),
        "created_at": record.created_at,
        "days": saved_plan,
    }