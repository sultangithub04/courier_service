from datetime import datetime, timedelta, timezone
import secrets
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(
    subject: str, user_id: int, role: str, token_type: str, expires_delta: timedelta
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "user_id": user_id,
        "role": role,
        "type": token_type,
        "iat": now,
        "jti": secrets.token_hex(16),
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM)


def create_access_token(user) -> str:
    return create_token(
        user.email,
        user.id,
        user.role.value,
        "access",
        timedelta(minutes=settings.jwt_access_token_expire_minutes),
    )


def create_refresh_token(user) -> str:
    return create_token(
        user.email,
        user.id,
        user.role.value,
        "refresh",
        timedelta(days=settings.jwt_refresh_token_expire_days),
    )


def decode_token(token: str, expected_type: str = "access") -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
        if payload.get("type") != expected_type:
            raise ValueError("Invalid token type")
        return payload
    except (JWTError, ValueError):
        raise ValueError("Invalid or expired token")
