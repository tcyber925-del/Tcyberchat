from sqlalchemy.orm import Session
from ..models.user import User, EmailVerification
from ..core.security import get_password_hash, verify_password
from datetime import datetime, timedelta, timezone
import secrets

# Use timezone.utc for consistency
UTC = timezone.utc

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: str):
    return db.query(User).filter(User.id == user_id).first()

def update_user_password(db: Session, user_id: str, new_password: str):
    user = get_user_by_id(db, user_id)
    if user:
        user.password_hash = get_password_hash(new_password)
        db.commit()
        return True
    return False

def create_user(db: Session, user_create):
    hashed_password = get_password_hash(user_create.password)
    db_user = User(
        email=user_create.email, 
        password_hash=hashed_password,
        is_verified=True  # Auto-verify for now as email sending is TODO
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

def create_verification_token(db: Session, user_id: str):
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(hours=24)
    
    db_token = EmailVerification(token=token, user_id=user_id, expires_at=expires_at)
    db.add(db_token)
    db.commit()
    return token

def verify_email(db: Session, token: str):
    verification = db.query(EmailVerification).filter(EmailVerification.token == token).first()
    if not verification:
        return False
    
    # Check expiration
    now = datetime.now(UTC)
    expires = verification.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
        
    if expires < now:
        return False
    
    user = db.query(User).filter(User.id == verification.user_id).first()
    if user:
        user.is_verified = True
        db.delete(verification)
        db.commit()
        return True
    return False

def get_or_create_oauth_user(db: Session, email: str, provider: str = "google"):
    user = get_user_by_email(db, email)
    if user:
        # If user exists but has a different provider, we might want to update it 
        # or merge accounts. For simplicity, we just return the user.
        # Ensure they are verified if they logged in via OAuth
        if not user.is_verified:
            user.is_verified = True
            db.commit()
        return user
    
    # Create new user
    new_user = User(
        email=email,
        password_hash=None, # No password for OAuth users
        is_verified=True,
        provider=provider
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user