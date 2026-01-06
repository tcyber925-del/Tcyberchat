from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth.dependencies import get_current_user
from ..models.user import User
from ..services.usage_service import get_usage_service

router = APIRouter(prefix="/usage", tags=["usage"])

@router.get("/")
async def get_usage_stats(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Get current user's usage stats and quota limits"""
    usage_service = get_usage_service(db)
    quota = usage_service.get_or_create_quota(str(current_user.id))
    
    # Trigger a check to ensure reset logic runs if needed
    try:
        usage_service.check_quota(str(current_user.id))
    except Exception:
        # Ignore limit exceptions here, we just want to update the reset date if needed
        pass
        
    return {
        "tier": quota.tier,
        "requests": {
            "used": quota.requests_used,
            "limit": quota.daily_request_limit,
            "remaining": max(0, quota.daily_request_limit - quota.requests_used)
        },
        "tokens": {
            "used": quota.tokens_used,
            "limit": quota.daily_token_limit,
            "remaining": max(0, quota.daily_token_limit - quota.tokens_used)
        },
        "reset_date": quota.last_reset_date
    }
