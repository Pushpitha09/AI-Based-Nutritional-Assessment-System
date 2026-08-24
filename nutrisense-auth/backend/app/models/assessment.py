from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    features_json = Column(String, nullable=False)   # the 13 features sent to the model
    risks_json = Column(String, nullable=False)       # the 10 label -> probability results
    overall_score = Column(Float, nullable=False)      # wellness score, 0-100
    diary_days_used = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
