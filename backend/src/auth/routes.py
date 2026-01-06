from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from ..database import get_db
from .schemas import UserCreate, UserLogin, Token, ForgotPasswordRequest, PasswordResetConfirm
from . import service, tokens
from ..core.config import settings
from ..core.redis import redis_client
import secrets
from .dependencies import get_current_user_id
from .oauth import get_google_auth_url, get_google_user_info
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    # TODO: Add rate limiting here
    db_user = service.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = service.create_user(db=db, user_create=user)
    
    # Create verification token
    token = service.create_verification_token(db, new_user.id)
    
    # TODO: Send actual email
    # For dev/demo, we can print it or return it (careful in prod)
    print(f"DEV: Verification token for {new_user.email}: {token}")
    
    return {"message": "User created. Please check your email to verify."}

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # TODO: Add rate limiting
    user = service.get_user_by_email(db, email=request.email)
    if not user:
        # Return success even if email not found for security
        return {"message": "If this email is registered, you will receive a reset link."}
    
    token = secrets.token_urlsafe(32)
    # Store in Redis for 15 mins (900 seconds)
    await redis_client.setex(f"password_reset:{token}", 900, str(user.id))
    
    # TODO: Send actual email
    print(f"DEV: Password reset link for {user.email}: /reset-password?token={token}")
    
    return {"message": "If this email is registered, you will receive a reset link."}

@router.post("/reset-password")
async def reset_password(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    user_id = await redis_client.get(f"password_reset:{data.token}")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Update password
    service.update_user_password(db, user_id, data.new_password)
    
    # Clean up token
    await redis_client.delete(f"password_reset:{data.token}")
    
    return {"message": "Password reset successfully"}

@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    # TODO: Add rate limiting
    success = service.verify_email(db, token)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    return {"message": "Email verified successfully"}

@router.post("/login")
def login(response: Response, user_in: UserLogin, db: Session = Depends(get_db)):
    # TODO: Add rate limiting
    user = service.authenticate_user(db, user_in.email, user_in.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    if not user.is_verified:
         raise HTTPException(status_code=403, detail="Email not verified")
    
    access_token = tokens.create_access_token(data={"sub": str(user.id)})
    refresh_token = tokens.create_refresh_token()
    
    # Store refresh token in Redis
    # Key: refresh:{token}, Value: user_id, TTL: REFRESH_TOKEN_EXPIRE_DAYS
    redis_client.setex(
        f"refresh:{refresh_token}", 
        settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600, 
        str(user.id)
    )

    # Set cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False, # Set to True if using HTTPS in dev/prod
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False, # Set to True if using HTTPS
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
    )
    
    return {"message": "Logged in successfully"}

@router.post("/refresh")
async def refresh(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    
    user_id = await redis_client.get(f"refresh:{refresh_token}")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    new_access_token = tokens.create_access_token(data={"sub": str(user_id)})
    
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return {"message": "Token refreshed"}

@router.post("/logout")
async def logout(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        await redis_client.delete(f"refresh:{refresh_token}")
    
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}

@router.get("/google")
async def google_login():
    """Redirect to Google OAuth consent screen"""
    return {"url": get_google_auth_url()}

@router.get("/google/callback")
async def google_callback(code: str, response: Response, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    user_info, error = await get_google_user_info(code)
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    email = user_info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="No email provided by Google")
        
    user = service.get_or_create_oauth_user(db, email, provider="google")
    
    # Issue tokens
    access_token = tokens.create_access_token(data={"sub": str(user.id)})
    refresh_token = tokens.create_refresh_token()
    
    redis_client.setex(
        f"refresh:{refresh_token}", 
        settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600, 
        str(user.id)
    )

    # Set cookies
    # Note: When called via browser redirect, this needs to be a RedirectResponse
    # But since we are using a proxy or frontend handler, we might return JSON + Cookies 
    # OR redirect to the frontend app.
    # Let's redirect to the frontend home page with cookies set.
    
    response = RedirectResponse(url="/")
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
    )
    return response

@router.get("/me")
async def get_me(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
