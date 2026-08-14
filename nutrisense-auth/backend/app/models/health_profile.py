from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.database import Base


class HealthProfile(Base):
    __tablename__ = "health_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    age = Column(Integer, nullable=False)
    gender = Column(Integer, nullable=False)  # 1 = Male, 2 = Female
    height_cm = Column(Float, nullable=False)
    weight_kg = Column(Float, nullable=False)
    activity_level = Column(String, nullable=False)  # sedentary/lightly_active/moderately_active/very_active
    health_goal = Column(String, default="")
    dietary_restrictions = Column(String, default="")  # comma-separated: "vegetarian,gluten_free"

    created_at = Column(DateTime(timezone=True), server_default=func.now())
