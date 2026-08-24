import json
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.assessment import Assessment
from app.models.user import User
from app.schemas import AssessmentOut, AssessmentHistoryItem
from app.routers.auth_router import get_current_user
from app.services.assess_service import run_assessment, build_recommendations, AssessmentError


router = APIRouter(prefix="/assess", tags=["assessment"])


@router.post("", response_model=AssessmentOut)
def create_assessment(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result = run_assessment(db, current_user.id)

    except AssessmentError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    today = date.today()

    existing_record = (
        db.query(Assessment)
        .filter(
            Assessment.user_id == current_user.id,
            func.date(Assessment.created_at) == today
        )
        .first()
    )

    if existing_record:
        existing_record.features_json = json.dumps(
            result["features"]
        )

        existing_record.risks_json = json.dumps(
            result["risks"]
        )

        existing_record.overall_score = result[
            "overall_score"
        ]

        existing_record.diary_days_used = result[
            "diary_days_used"
        ]

    else:
        record = Assessment(
            user_id=current_user.id,
            features_json=json.dumps(result["features"]),
            risks_json=json.dumps(result["risks"]),
            overall_score=result["overall_score"],
            diary_days_used=result["diary_days_used"],
        )

        db.add(record)

    db.commit()

    return AssessmentOut(
        overall_score=result["overall_score"],
        diary_days_used=result["diary_days_used"],
        risks=result["risks"],
        features=result["features"],
        recommendations=result["recommendations"],
    )

    # Otherwise, run a new assessment
    try:
        result = run_assessment(db, current_user.id)

    except AssessmentError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    # Save the new assessment
    record = Assessment(
        user_id=current_user.id,
        features_json=json.dumps(result["features"]),
        risks_json=json.dumps(result["risks"]),
        overall_score=result["overall_score"],
        diary_days_used=result["diary_days_used"],
    )

    db.add(record)
    db.commit()

    return AssessmentOut(
        overall_score=result["overall_score"],
        diary_days_used=result["diary_days_used"],
        risks=result["risks"],
        features=result["features"],
        recommendations=result["recommendations"],
    )

@router.get("/latest", response_model=AssessmentOut)
def get_latest_assessment(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = (
        db.query(Assessment)
        .filter(Assessment.user_id == current_user.id)
        .order_by(Assessment.created_at.desc())
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="No assessment has been run yet.")

    risks = json.loads(record.risks_json)
    # Recomputed fresh each time (not stored) so recommendations reflect the
    # current food database and current dietary restrictions, not whatever
    # they were at the moment the assessment was originally run.
    recommendations = build_recommendations(db, current_user.id, risks)

    return AssessmentOut(
        overall_score=record.overall_score,
        diary_days_used=record.diary_days_used,
        risks=risks,
        features=json.loads(record.features_json),
        recommendations=recommendations,
    )

@router.get("/history", response_model=list[AssessmentHistoryItem])
def get_assessment_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    records = (
        db.query(Assessment)
        .filter(Assessment.user_id == current_user.id)
        .order_by(Assessment.created_at.asc())
        .all()
    )

    return records
