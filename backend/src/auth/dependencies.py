from fastapi import Request, HTTPException, Depends, status
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..core.config import settings

def get_current_user_id(request: Request) -> str:
    token = request.cookies.get("access_token")
    if not token:
        # Check Authorization header as fallback
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def get_current_user(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> User | None:
    """
    Optional authentication dependency.
    Returns User object if authenticated, None otherwise.
    Does NOT raise HTTPException for missing credentials.
    """
    try:
        user_id = get_current_user_id(request)
        return db.query(User).filter(User.id == user_id).first()
    except HTTPException:
        return None
