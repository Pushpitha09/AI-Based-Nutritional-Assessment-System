from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth_router, profile_router, food_router, diary_router, lab_router

# Import all models so SQLAlchemy knows about every table before create_all runs
from app.models.user import User  # noqa: F401
from app.models.health_profile import HealthProfile  # noqa: F401
from app.models.food_item import FoodItem  # noqa: F401
from app.models.diary_entry import DiaryEntry  # noqa: F401
from app.models.lab_result import LabResult  # noqa: F401

# Creates all tables in nutrisense.db if they don't exist yet
Base.metadata.create_all(bind=engine)

app = FastAPI(title="NutriSense Backend")

# Allow the React frontend (running on a different port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # default Vite dev server port
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(profile_router.router)
app.include_router(food_router.router)
app.include_router(diary_router.router)
app.include_router(lab_router.router)


@app.get("/")
def read_root():
    return {"message": "NutriSense backend is running!"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
