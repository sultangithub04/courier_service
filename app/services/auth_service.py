import hashlib,secrets
from datetime import datetime,timedelta,timezone
from app.core.config import settings
from app.core.security import hash_password,verify_password,create_access_token,create_refresh_token,decode_token
from app.models import User,Role,UserStatus,RefreshToken,PasswordResetToken
def signup(db,data):
    if db.query(User).filter(User.email==data.email).first(): raise ValueError("Email already registered")
    user=User(name=data.name,email=data.email,phone=data.phone,password_hash=hash_password(data.password),role=Role.USER,status=UserStatus.ACTIVE)
    db.add(user); db.commit(); db.refresh(user); return user
def authenticate(db,email,password):
    user=db.query(User).filter(User.email==email).first()
    if not user or not verify_password(password,user.password_hash) or user.status!=UserStatus.ACTIVE: return None
    return user
def issue_tokens(db,user):
    access=create_access_token(user); refresh=create_refresh_token(user)
    payload=decode_token(refresh,"refresh")
    db.add(RefreshToken(user_id=user.id,token_jti=payload.get("jti",secrets.token_hex(16)),expires_at=datetime.fromtimestamp(payload["exp"],timezone.utc)))
    db.commit(); return access,refresh
def refresh_tokens(db,token):
    try: payload=decode_token(token,"refresh")
    except ValueError: raise ValueError("Invalid or expired refresh token")
    record=db.query(RefreshToken).filter(RefreshToken.token_jti==payload.get("jti")).first()
    user=db.get(User,int(payload["user_id"]))
    if not record or record.revoked or not user or user.status!=UserStatus.ACTIVE: raise ValueError("Refresh token revoked or invalid")
    record.revoked=True; db.commit(); return issue_tokens(db,user)
def create_reset_token(db,user):
    raw=secrets.token_urlsafe(48); hashed=hashlib.sha256(raw.encode()).hexdigest()
    db.add(PasswordResetToken(user_id=user.id,token_hash=hashed,expires_at=datetime.now(timezone.utc)+timedelta(minutes=30))); db.commit()
    return raw
def reset_password(db,raw,new_password):
    hashed=hashlib.sha256(raw.encode()).hexdigest()
    rec=db.query(PasswordResetToken).filter(PasswordResetToken.token_hash==hashed,PasswordResetToken.used==False).first()
    if not rec or rec.expires_at < datetime.now(timezone.utc): raise ValueError("Invalid or expired reset token")
    user=db.get(User,rec.user_id); user.password_hash=hash_password(new_password); rec.used=True; db.commit()


def send_reset_email(email, token):
    # Email provider integration point. Return False until SMTP/provider is configured.
    return False
