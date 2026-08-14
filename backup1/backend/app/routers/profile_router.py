from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.health_profile import HealthProfile
from app.models.user import User
from app.schemas import OnboardingRequest, HealthProfileOut
from app.routers.auth_router import get_current_user

router = APIRouter(prefix="/profile", tags=["profile"])


@router.post("/onboarding", response_model=HealthProfileOut)
def submit_onboarding(
    payload: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(HealthProfile).filter(HealthProfile.user_id == current_user.id).first()

    restrictions_str = ",".join(payload.dietary_restrictions)

    if existing:
        existing.age = payload.age
        existing.gender = payload.gender
        existing.height_cm = payload.height_cm
        existing.weight_kg = payload.weight_kg
        existing.activity_level = payload.activity_level
        existing.dietary_restrictions = restrictions_str
        profile = existing
    else:
        profile = HealthProfile(
            user_id=current_user.id,
            age=payload.age,
            gender=payload.gender,
            height_cm=payload.height_cm,
            weight_kg=payload.weight_kg,
            activity_level=payload.activity_level,
            dietary_restrictions=restrictions_str,
        )
        db.add(profile)

    db.commit()
    db.refresh(profile)
    return profile


@router.get("/me", response_model=HealthProfileOut)
def get_my_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(HealthProfile).filter(HealthProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No health profile found for this user yet")
    return profile
