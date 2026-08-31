# food_tags.py

"""
Food-quality and dietary restriction helpers.

These functions are used ONLY for filtering and improving food
recommendations. They do NOT affect:

- diary nutrient calculations
- ML assessment predictions
- wellness score
- lab result boosts
"""

import re


# ============================================================
# DIETARY CLASSIFICATION
# ============================================================

MEAT_KEYWORDS = [
    "chicken",
    "beef",
    "pork",
    "fish",
    "shrimp",
    "mutton",
    "lamb",
    "turkey",
    "bacon",
    "ham",
    "salmon",
    "tuna",
    "meat",
    "gelatin",
    "prawn",
    "crab",
    "goat",
    "duck",
    "sausage",
    "frankfurter",
    "anchovy",
    "oyster",
    "squid",
    "liver",
    "gizzard",
    "veal",
    "clam",
    "mussel",
    "lobster",
    "shellfish",
    "cod",
    "sardine",
    "mackerel",
    "trout",
    "herring",
    "cuttlefish",
    "mollusks",
]


EGG_KEYWORDS = [
    "egg",
]


DAIRY_KEYWORDS = [
    "milk",
    "cheese",
    "paneer",
    "curd",
    "yogurt",
    "yoghurt",
    "ghee",
    "butter",
    "cream",
    "whey",
    "casein",
    "buttermilk",
    "khoya",
]


GLUTEN_KEYWORDS = [
    "wheat",
    "roti",
    "bread",
    "barley",
    "rye",
    "maida",
    "biscuit",
    "cookie",
    "pasta",
    "noodle",
    "cake",
    "bun",
    "cracker",
    "pretzel",
    "chapati",
    "naan",
    "paratha",
    "vermicelli",
    "semolina",
    "rava",
]


NUT_KEYWORDS = [
    "almond",
    "walnut",
    "cashew",
    "peanut",
    "pistachio",
    "hazelnut",
    "pecan",
    "macadamia",
]


def _contains_keyword(name: str, keyword: str) -> bool:
    """
    Match complete words to avoid accidental matches.
    """

    pattern = rf"\b{re.escape(keyword.lower())}\b"

    return bool(
        re.search(
            pattern,
            name.lower(),
        )
    )


def classify_food(name: str) -> dict:
    """
    Infer dietary properties from the food name.

    This is a heuristic because USDA/IFCT data does not provide
    consistent dietary/allergen labels.
    """

    is_meat = any(
        _contains_keyword(name, keyword)
        for keyword in MEAT_KEYWORDS
    )

    is_egg = any(
        _contains_keyword(name, keyword)
        for keyword in EGG_KEYWORDS
    )

    is_dairy = any(
        _contains_keyword(name, keyword)
        for keyword in DAIRY_KEYWORDS
    )

    contains_gluten = any(
        _contains_keyword(name, keyword)
        for keyword in GLUTEN_KEYWORDS
    )

    contains_nuts = any(
        _contains_keyword(name, keyword)
        for keyword in NUT_KEYWORDS
    )

    is_vegetarian = not (
        is_meat
        or is_egg
    )

    is_vegan = (
        is_vegetarian
        and not is_dairy
    )

    return {
        "is_vegetarian": is_vegetarian,
        "is_vegan": is_vegan,
        "contains_dairy": is_dairy,
        "contains_gluten": contains_gluten,
        "contains_nuts": contains_nuts,
    }


# ============================================================
# USER DIETARY RESTRICTIONS
# ============================================================

VALID_RESTRICTIONS = {
    "vegetarian",
    "vegan",
    "gluten_free",
    "dairy_free",
    "nut_allergy",
}


def normalize_restrictions(restrictions):
    """
    Normalize dietary restrictions.

    Example:

    [" Vegetarian ", "DAIRY_FREE"]

    becomes:

    ["vegetarian", "dairy_free"]
    """

    return [
        restriction.strip().lower()
        for restriction in restrictions
        if restriction.strip().lower()
        in VALID_RESTRICTIONS
    ]


def food_matches_restrictions(
    food,
    restrictions,
) -> bool:
    """
    Check whether a food is compatible with the user's
    dietary restrictions.

    Classification is based on the food name rather than
    relying on stored database tags.
    """

    if not restrictions:
        return True

    name = getattr(
        food,
        "name",
        "",
    )

    classified = classify_food(name)

    if (
        "vegetarian" in restrictions
        and not classified["is_vegetarian"]
    ):
        return False

    if (
        "vegan" in restrictions
        and not classified["is_vegan"]
    ):
        return False

    if (
        "dairy_free" in restrictions
        and classified["contains_dairy"]
    ):
        return False

    if (
        "gluten_free" in restrictions
        and classified["contains_gluten"]
    ):
        return False

    if (
        "nut_allergy" in restrictions
        and classified["contains_nuts"]
    ):
        return False

    return True


# ============================================================
# FOOD QUALITY FILTERING
# ============================================================

POOR_RECOMMENDATION_TERMS = [

    # Cooking ingredients / additives
    "baking powder",
    "leavening agent",
    "leavening agents",
    "table salt",
    "salt substitute",
    "seasoning",
    "flavoring",
    "flavouring",
    "extract",
    "food coloring",
    "food colouring",
    "gelatin dry",
    "yeast extract",

    # Spices and herbs
    "spices,",
    "paprika",
    "marjoram",
    "spearmint",
    "chives",
    "seasoning mix",

    # Powders / mixes / preparation ingredients
    "powder",
    "dry mix",
    "unprepared",
    "not reconstituted",

    # Infant foods
    "infant formula",
    "babyfood",
    "baby food",
    "toddler",

    # Raw animal products
    ", raw",
    "raw,",

    # Organ foods
    "giblet",
    "gizzard",
    "kidney",
    "brain",
    "tripe",
    "tongue",

    # Processed organ products
    "liver sausage",
    "liverwurst",
    "braunschweiger",
    "liver cheese",
    "pate",

    # Other unsuitable items
    "margarine",
    "whey, acid",
]


def is_good_recommendation_food(name: str) -> bool:
    """
    Returns False for database entries that should not be
    displayed as normal foods or used in meal plans.

    This does NOT affect diary calculations or ML assessment.
    """

    name_lower = name.lower()

    return not any(
        term in name_lower
        for term in POOR_RECOMMENDATION_TERMS
    )


# ============================================================
# FOOD QUALITY SCORING
# ============================================================

PREFERRED_FOOD_KEYWORDS = [

    # Vegetables
    "spinach",
    "carrot",
    "broccoli",
    "tomato",
    "capsicum",
    "sweet potato",
    "drumstick",
    "agathi",
    "pumpkin",

    # Fruits
    "orange",
    "guava",
    "papaya",
    "mango",
    "banana",
    "apple",
    "berries",

    # Legumes / plant protein
    "lentil",
    "chickpea",
    "bean",
    "pea",
    "tofu",
    "soy",

    # Nuts / seeds
    "almond",
    "walnut",
    "cashew",
    "sesame",
    "chia",
    "flaxseed",
    "pumpkin seed",
    "sunflower seed",

    # Dairy
    "milk",
    "curd",
    "yogurt",
    "yoghurt",
    "paneer",
    "cheese",

    # Eggs
    "egg",

    # Fish
    "salmon",
    "tuna",
    "sardine",
    "mackerel",
    "trout",
    "cod",
    "fish",

    # Meat
    "chicken",
    "beef",
    "lamb",

    # Grains
    "ragi",
    "finger millet",
    "bajra",
    "jowar",
    "oat",
]


def food_quality_score(name: str) -> int:
    """
    Gives recognizable normal foods a small ranking bonus.

    Nutrient values remain the primary ranking factor.
    """

    name_lower = name.lower()

    score = 0

    for keyword in PREFERRED_FOOD_KEYWORDS:
        if keyword in name_lower:
            score += 1

    if len(name) < 60:
        score += 1

    return score


# ============================================================
# DUPLICATE NORMALIZATION
# ============================================================

def get_food_key(name: str) -> str:
    """
    Create a simplified key to avoid showing nearly identical
    versions of the same food.
    """

    name_lower = name.lower()

    remove_terms = [
        "with added vitamin a",
        "without added vitamin a",
        "with added vitamin d",
        "without added vitamin d",
        "vitamin d fortified",
        "regular",
        "instant",
        "prepared",
        "cooked",
        "raw",
        "frozen",
        "canned",
        "dried",
        "dry",
    ]

    for term in remove_terms:
        name_lower = name_lower.replace(
            term,
            "",
        )

    name_lower = re.sub(
        r"[^a-z0-9\s]",
        " ",
        name_lower,
    )

    name_lower = re.sub(
        r"\s+",
        " ",
        name_lower,
    ).strip()

    words = name_lower.split()

    return " ".join(
        words[:4]
    )

