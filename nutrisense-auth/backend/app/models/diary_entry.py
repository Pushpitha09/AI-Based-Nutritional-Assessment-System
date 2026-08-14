from sqlalchemy import Column, Integer, Float, String, Date, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.database import Base


class DiaryEntry(Base):
    __tablename__ = "diary_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)

    entry_date = Column(Date, nullable=False)
    meal = Column(String, nullable=False)  # breakfast/lunch/dinner/snack
    portion_grams = Column(Float, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
