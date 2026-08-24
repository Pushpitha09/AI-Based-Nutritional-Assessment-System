import re
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime


from pydantic import BaseModel, EmailStr, field_validator


def validate_password_strength(password: str) -> str:
    """
    Password must have:
    - at least 8 characters
    - at least 1 uppercase letter
    - at least 1 lowercase letter
    - at least 1 number
    - at least 1 special character
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"[0-9]", password):
        raise ValueError("Password must contain at least one number")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError("Password must contain at least one special character")
    return password


class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    confirm_password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        return validate_password_strength(v)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class UserUpdateRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v):
        return validate_password_strength(v)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


# --- Onboarding / health profile ---

class OnboardingRequest(BaseModel):
    age: int
    gender: int  # 1 = Male, 2 = Female
    height_cm: float
    weight_kg: float
    activity_level: str
    health_goal: str = ""
    dietary_restrictions: list[str] = []

    @field_validator("gender")
    @classmethod
    def gender_must_be_1_or_2(cls, v):
        if v not in (1, 2):
            raise ValueError("gender must be 1 (Male) or 2 (Female)")
        return v

    @field_validator("age")
    @classmethod
    def age_reasonable(cls, v):
        if not (1 <= v <= 120):
            raise ValueError("age must be between 1 and 120")
        return v


class HealthProfileOut(BaseModel):
    age: int
    gender: int
    height_cm: float
    weight_kg: float
    activity_level: str
    health_goal: str
    dietary_restrictions: str

    class Config:
        from_attributes = True


# --- Lab results ---

class LabResultRequest(BaseModel):
    hemoglobin_g_dl: float | None = None
    serum_vitamin_d: float | None = None
    ferritin: float | None = None
    vitamin_b12: float | None = None
    calcium: float | None = None


class LabResultOut(BaseModel):
    hemoglobin_g_dl: float | None
    serum_vitamin_d: float | None
    ferritin: float | None
    vitamin_b12: float | None
    calcium: float | None

    class Config:
        from_attributes = True


# --- Assessment ---

class RiskItemOut(BaseModel):
    label: str
    nutrient: str
    probability: float
    predicted_deficient: bool
    ui_percent: int
    ui_level: str
    tag: str | None


class RecommendedFoodOut(BaseModel):
    name: str
    amount: float


class AssessmentOut(BaseModel):
    overall_score: float
    diary_days_used: int
    risks: list[RiskItemOut]
    features: dict
    recommendations: dict[str, list[RecommendedFoodOut]] = {}

class AssessmentHistoryItem(BaseModel):
    id: int
    overall_score: float
    diary_days_used: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Food search ---

class FoodItemOut(BaseModel):
    id: int
    name: str
    calories_kcal: float
    protein_g: float
    iron_mg: float
    calcium_mg: float
    vitamin_d_mcg: float
    vitamin_b12_mcg: float
    folate_mcg: float
    vitamin_a_mcg: float
    vitamin_c_mg: float
    magnesium_mg: float
    zinc_mg: float

    class Config:
        from_attributes = True


# --- Diary entries ---

class DiaryEntryCreate(BaseModel):
    entry_date: str  # "YYYY-MM-DD"
    meal: str
    food_item_id: int
    portion_grams: float


class DiaryEntryOut(BaseModel):
    id: int
    entry_date: str
    meal: str
    portion_grams: float
    food_name: str

    calories_kcal: float
    protein_g: float
    iron_mg: float
    calcium_mg: float
    vitamin_d_mcg: float
    vitamin_b12_mcg: float
    folate_mcg: float
    vitamin_a_mcg: float
    vitamin_c_mg: float
    magnesium_mg: float
    zinc_mg: float