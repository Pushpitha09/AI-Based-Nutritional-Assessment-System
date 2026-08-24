import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Use the isolated food database by default. Override it with
# NUTRISENSE_DATABASE_FILE when another local database is needed.
DATABASE_FILE = os.getenv("NUTRISENSE_DATABASE_FILE", "nutrisense_fresh.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///./{DATABASE_FILE}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # needed only for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Dependency used by FastAPI routes to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
