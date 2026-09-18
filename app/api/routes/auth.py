from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from app.api.dependencies import DB, CurrentUser
from app.core.rate_limit import auth_rate_limit
from fastapi import Depends
from app.core.security import verify_password, hash_password, decode_token
from app.schemas.auth import *
from app.services import auth_service
from app.models import RefreshToken, User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=201,
    dependencies=[Depends(auth_rate_limit)],
)
def signup(data: SignupRequest, db: DB):
    try:
        return auth_service.signup(db, data)
    except ValueError as e:
        raise HTTPException(409, str(e))


@router.post(
    "/login", response_model=TokenResponse, dependencies=[Depends(auth_rate_limit)]
)
def login(data: LoginRequest, db: DB):
    user = auth_service.authenticate(db, data.email, data.password)
    if not user:
        raise HTTPException(401, "Invalid email or password")
    access, refresh = auth_service.issue_tokens(db, user)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, db: DB):
    try:
        a, r = auth_service.refresh_tokens(db, data.refresh_token)
        return TokenResponse(access_token=a, refresh_token=r)
    except ValueError as e:
        raise HTTPException(401, str(e))


@router.post("/logout")
def logout(data: RefreshRequest, db: DB):
    try:
        p = decode_token(data.refresh_token, "refresh")
    except ValueError:
        return {"success": True, "message": "Logged out"}
    rec = db.query(RefreshToken).filter(RefreshToken.token_jti == p.get("jti")).first()
    if rec:
        rec.revoked = True
        db.commit()
    return {"success": True, "message": "Logged out"}


@router.get("/me", response_model=UserResponse)
def me(user: CurrentUser):
    return user


@router.patch("/me", response_model=UserResponse)
def update_me(data: UpdateProfile, user: CurrentUser, db: DB):
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user


@router.post("/change-password")
def change_password(data: ChangePassword, user: CurrentUser, db: DB):
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(400, "Current password is incorrect")
    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"success": True, "message": "Password updated successfully"}


@router.post("/forgot-password", dependencies=[Depends(auth_rate_limit)])
def forgot(data: ForgotPasswordRequest, db: DB):
    user = db.query(User).filter(User.email == data.email).first()
    # Do not disclose whether the account exists.
    response = {
        "success": True,
        "message": "If the email exists, a password reset link will be sent.",
    }
    if user and user.status.value == "ACTIVE":
        token = auth_service.create_reset_token(db, user)
        if not auth_service.send_reset_email(user.email, token):
            # Development only: never expose this token in production.
            if (
                __import__("app.core.config", fromlist=["settings"]).settings.app_env
                == "development"
            ):
                response["reset_token_dev_only"] = token
    return response


@router.post("/reset-password", dependencies=[Depends(auth_rate_limit)])
def reset(data: ResetPasswordRequest, db: DB):
    try:
        auth_service.reset_password(db, data.token, data.new_password)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"success": True, "message": "Password reset successfully"}
