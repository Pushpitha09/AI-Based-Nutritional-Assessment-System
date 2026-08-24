from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.routers.auth_router import get_current_user
from app.services.meal_plan_service import generate_meal_plan, get_latest_meal_plan

router = APIRouter(prefix="/meal-plan", tags=["meal-plan"])


@router.get("/latest")
def latest_meal_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = get_latest_meal_plan(db, current_user.id)
    if not plan:
        raise HTTPException(status_code=404, detail="No meal plan has been generated yet.")
    return plan


@router.post("/regenerate")
def regenerate_meal_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return generate_meal_plan(db, current_user.id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
