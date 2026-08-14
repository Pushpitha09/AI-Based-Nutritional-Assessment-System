from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.diary_entry import DiaryEntry
from app.models.food_item import FoodItem
from app.models.user import User
from app.schemas import DiaryEntryCreate, DiaryEntryOut
from app.routers.auth_router import get_current_user

router = APIRouter(prefix="/diary", tags=["diary"])


@router.post("/entries", response_model=DiaryEntryOut)
def add_entry(
    payload: DiaryEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    food = db.query(FoodItem).filter(FoodItem.id == payload.food_item_id).first()
    if not food:
        raise HTTPException(status_code=404, detail="Food item not found")

    try:
        parsed_date = date_type.fromisoformat(payload.entry_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="entry_date must be in YYYY-MM-DD format")

    entry = DiaryEntry(
        user_id=current_user.id,
        food_item_id=payload.food_item_id,
        entry_date=parsed_date,
        meal=payload.meal,
        portion_grams=payload.portion_grams,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    ratio = payload.portion_grams / 100.0
    return DiaryEntryOut(
        id=entry.id,
        entry_date=payload.entry_date,
        meal=entry.meal,
        portion_grams=entry.portion_grams,
        food_name=food.name,
        calories_kcal=round(food.calories_kcal * ratio, 1),
        iron_mg=round(food.iron_mg * ratio, 2),
    )


@router.get("/entries", response_model=list[DiaryEntryOut])
def list_entries(
    entry_date: str = Query(..., description="YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        parsed_date = date_type.fromisoformat(entry_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="entry_date must be in YYYY-MM-DD format")

    rows = (
        db.query(DiaryEntry, FoodItem)
        .join(FoodItem, DiaryEntry.food_item_id == FoodItem.id)
        .filter(DiaryEntry.user_id == current_user.id, DiaryEntry.entry_date == parsed_date)
        .order_by(DiaryEntry.created_at)
        .all()
    )

    results = []
    for entry, food in rows:
        ratio = entry.portion_grams / 100.0
        results.append(
            DiaryEntryOut(
                id=entry.id,
                entry_date=entry_date,
                meal=entry.meal,
                portion_grams=entry.portion_grams,
                food_name=food.name,
                calories_kcal=round(food.calories_kcal * ratio, 1),
                iron_mg=round(food.iron_mg * ratio, 2),
            )
        )
    return results


@router.delete("/entries/{entry_id}")
def delete_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = (
        db.query(DiaryEntry)
        .filter(DiaryEntry.id == entry_id, DiaryEntry.user_id == current_user.id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(entry)
    db.commit()
    return {"deleted": True}
