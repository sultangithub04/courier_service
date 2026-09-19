
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import DB, CurrentUser
from app.core.rate_limit import auth_rate_limit
from app.core.security import (
    verify_password,
    hash_password,
    decode_token,
)
from app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
    UpdateProfile,
    ChangePassword,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.services import auth_service
from app.models import RefreshToken, User


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# ============================================================
# SIGNUP
# ============================================================

@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=201,
    dependencies=[Depends(auth_rate_limit)],
)
def signup(
    data: SignupRequest,
    db: DB,
):
    try:
        return auth_service.signup(
            db,
            data,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e),
        )


# ============================================================
# LOGIN
# ============================================================

@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(auth_rate_limit)],
)
def login(
    data: LoginRequest,
    db: DB,
):
    user = auth_service.authenticate(
        db,
        data.email,
        data.password,
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    access, refresh = auth_service.issue_tokens(
        db,
        user,
    )



    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user=user,
    )


# ============================================================
# REFRESH
# ============================================================

@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh(
    data: RefreshRequest,
    db: DB,
):
    try:
        access, refresh_token = auth_service.refresh_tokens(
            db,
            data.refresh_token,
        )

        # Keep your existing refresh-token service behavior.
        #
        # If TokenResponse requires user, we need to find
        # the user from the refresh token.

        payload = decode_token(
            refresh_token,
            "refresh",
        )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token",
            )

        user = (
            db.query(User)
            .filter(User.id == int(user_id))
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not found",
            )

        return TokenResponse(
            access_token=access,
            refresh_token=refresh_token,
            user=user,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
        )


# ============================================================
# LOGOUT
# ============================================================

@router.post("/logout")
def logout(
    data: RefreshRequest,
    db: DB,
):
    try:
        payload = decode_token(
            data.refresh_token,
            "refresh",
        )

    except ValueError:
        return {
            "success": True,
            "message": "Logged out",
        }

    token_jti = payload.get("jti")

    if token_jti:
        record = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.token_jti == token_jti
            )
            .first()
        )

        if record:
            record.revoked = True
            db.commit()

    return {
        "success": True,
        "message": "Logged out",
    }


# ============================================================
# CURRENT USER
# ============================================================

@router.get(
    "/me",
    response_model=UserResponse,
)
def me(
    user: CurrentUser,
):
    return user


# ============================================================
# UPDATE PROFILE
# ============================================================

@router.patch(
    "/me",
    response_model=UserResponse,
)
def update_me(
    data: UpdateProfile,
    user: CurrentUser,
    db: DB,
):
    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(
            user,
            field,
            value,
        )

    db.commit()
    db.refresh(user)

    return user


# ============================================================
# CHANGE PASSWORD
# ============================================================

@router.post("/change-password")
def change_password(
    data: ChangePassword,
    user: CurrentUser,
    db: DB,
):
    if not verify_password(
        data.current_password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect",
        )

    user.password_hash = hash_password(
        data.new_password
    )

    db.commit()

    return {
        "success": True,
        "message": "Password updated successfully",
    }


# ============================================================
# FORGOT PASSWORD
# ============================================================

@router.post(
    "/forgot-password",
    dependencies=[Depends(auth_rate_limit)],
)
def forgot(
    data: ForgotPasswordRequest,
    db: DB,
):
    user = (
        db.query(User)
        .filter(User.email == data.email)
        .first()
    )

    # Do not disclose whether the account exists.
    response = {
        "success": True,
        "message": (
            "If the email exists, a password reset "
            "link will be sent."
        ),
    }

    if user and user.status.value == "ACTIVE":
        token = auth_service.create_reset_token(
            db,
            user,
        )

        email_sent = auth_service.send_reset_email(
            user.email,
            token,
        )

        if not email_sent:
            from app.core.config import settings

            if settings.app_env == "development":
                response["reset_token_dev_only"] = token

    return response


# ============================================================
# RESET PASSWORD
# ============================================================

@router.post(
    "/reset-password",
    dependencies=[Depends(auth_rate_limit)],
)
def reset(
    data: ResetPasswordRequest,
    db: DB,
):
    try:
        auth_service.reset_password(
            db,
            data.token,
            data.new_password,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    return {
        "success": True,
        "message": "Password reset successfully",
    }

