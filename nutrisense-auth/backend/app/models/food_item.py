from sqlalchemy import Column, Integer, Float, String
from app.database import Base


class FoodItem(Base):
    """
    Per-100g nutrient values. Same nutrient set as the ML model's FEATURE_COLS,
    so a diary entry's totals line up directly with what the deficiency model expects.
    'source' distinguishes which dataset a row came from (usda / ifct / seed).
    """
    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    source = Column(String, default="seed")

    calories_kcal = Column(Float, default=0)
    protein_g = Column(Float, default=0)
    iron_mg = Column(Float, default=0)
    calcium_mg = Column(Float, default=0)
    vitamin_d_mcg = Column(Float, default=0)
    vitamin_b12_mcg = Column(Float, default=0)
    folate_mcg = Column(Float, default=0)
    vitamin_a_mcg = Column(Float, default=0)
    vitamin_c_mg = Column(Float, default=0)
    magnesium_mg = Column(Float, default=0)
    zinc_mg = Column(Float, default=0)
