from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.database import Base


class LabResult(Base):
    """
    Optional blood test values a user can enter themselves. One row per user
    (upsert on save) - this is their current/most-recent snapshot, not a
    history log. Matches the fields shown in the reference design: hemoglobin,
    serum vitamin D, ferritin, vitamin B12, calcium.
    All fields are nullable since entering labs is optional.
    """
    __tablename__ = "lab_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    hemoglobin_g_dl = Column(Float, nullable=True)
    serum_vitamin_d = Column(Float, nullable=True)
    ferritin = Column(Float, nullable=True)
    vitamin_b12 = Column(Float, nullable=True)
    calcium = Column(Float, nullable=True)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
