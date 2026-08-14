from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.lab_result import LabResult
from app.models.user import User
from app.schemas import LabResultRequest, LabResultOut
from app.routers.auth_router import get_current_user

router = APIRouter(prefix="/labs", tags=["labs"])


@router.post("", response_model=LabResultOut)
def save_labs(
    payload: LabResultRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(LabResult).filter(LabResult.user_id == current_user.id).first()

    if existing:
        existing.hemoglobin_g_dl = payload.hemoglobin_g_dl
        existing.serum_vitamin_d = payload.serum_vitamin_d
        existing.ferritin = payload.ferritin
        existing.vitamin_b12 = payload.vitamin_b12
        existing.calcium = payload.calcium
        record = existing
    else:
        record = LabResult(user_id=current_user.id, **payload.model_dump())
        db.add(record)

    db.commit()
    db.refresh(record)
    return record


@router.get("/me", response_model=LabResultOut)
def get_my_labs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = db.query(LabResult).filter(LabResult.user_id == current_user.id).first()
    if not record:
        # No labs entered yet - return all-empty rather than a 404,
        # since "no labs" is a normal, expected state (they're optional).
        return LabResultOut(
            hemoglobin_g_dl=None, serum_vitamin_d=None, ferritin=None,
            vitamin_b12=None, calcium=None,
        )
    return record
