from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.models import User, Role, UserStatus

security = HTTPBearer()
DB = Annotated[Session, Depends(get_db)]


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)], db: DB
) -> User:
    try:
        payload = decode_token(credentials.credentials, "access")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")
    user = db.get(User, int(payload["user_id"]))
    if not user or user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=401, detail="User is not active")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles):
    def checker(user: CurrentUser):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return checker


Admin = Annotated[User, Depends(require_roles(Role.ADMIN))]
Agent = Annotated[User, Depends(require_roles(Role.DELIVERY_AGENT))]
