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
    results = (
        db.query(FoodItem)
        .filter(FoodItem.name.ilike(f"%{q}%"))
        .order_by(FoodItem.name)
        .limit(limit)
        .all()
    )
    return results
