from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt

# --- Password hashing ---
# bcrypt is a one-way hash: we never store or can retrieve the real password,
# we only ever compare "does this new password hash match the stored hash?"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# --- JWT tokens (used to keep a user "logged in" after they authenticate) ---
# NOTE: in a real production app, this secret key should come from an
# environment variable, not be hardcoded. Fine for a student project.
SECRET_KEY = "nutrisense-dev-secret-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None
