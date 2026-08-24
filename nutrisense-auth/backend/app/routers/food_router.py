from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.food_item import FoodItem
from app.schemas import FoodItemOut
from app.routers.auth_router import get_current_user

router = APIRouter(prefix="/foods", tags=["foods"])


@router.get("/search", response_model=list[FoodItemOut])
def search_foods(
    q: str = Query(..., min_length=1),
    limit: int = 8,
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    # Pull a wider pool than we'll actually return, then rank it ourselves -
    # a plain alphabetical DB order means "Bagels, egg" beats "Egg, whole"
    # just because B < E, even though the second is what someone typing
    # "egg" almost certainly means.
    candidates = (
        db.query(FoodItem)
        .filter(FoodItem.name.ilike(f"%{q}%"))
        .order_by(FoodItem.name)
        .limit(limit * 20)
        .all()
    )

    q_lower = q.lower()

    def relevance_key(food):
        name_lower = food.name.lower()
        if name_lower == q_lower:
            tier = 0                          # exact match
        elif name_lower.startswith(q_lower):
            tier = 1                          # starts with the search term
        elif f", {q_lower}" in name_lower or f" {q_lower}," in name_lower or f" {q_lower} " in name_lower:
            tier = 2                          # search term is its own "word" in the name
        else:
            tier = 3                          # search term buried inside another word/phrase
        return (tier, len(food.name), name_lower)  # shorter names break ties within a tier

    ranked = sorted(candidates, key=relevance_key)
    return ranked[:limit]
