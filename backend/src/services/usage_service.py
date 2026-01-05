from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.usage import UsageLog, UserQuota
from ..core.config import settings

class UsageService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_quota(self, user_id: str) -> UserQuota:
        quota = self.db.query(UserQuota).filter(UserQuota.user_id == user_id).first()
        if not quota:
            quota = UserQuota(
                user_id=user_id,
                daily_request_limit=settings.QUOTA_FREE_DAILY_REQUESTS,
                daily_token_limit=settings.QUOTA_FREE_DAILY_TOKENS
            )
            self.db.add(quota)
            self.db.commit()
            self.db.refresh(quota)
        return quota

    def check_quota(self, user_id: str):
        """Check if user has sufficient quota. Raises HTTPException if exceeded."""
        quota = self.get_or_create_quota(user_id)
        
        # Check reset (simplified daily reset based on UTC date)
        now = datetime.now(timezone.utc)
        if quota.last_reset_date.date() < now.date():
            quota.requests_used = 0
            quota.tokens_used = 0
            quota.last_reset_date = now
            self.db.commit()
        
        if quota.daily_request_limit > 0 and quota.requests_used >= quota.daily_request_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS, 
                detail="Daily request limit exceeded"
            )
            
        if quota.daily_token_limit > 0 and quota.tokens_used >= quota.daily_token_limit:
             raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS, 
                detail="Daily token limit exceeded"
            )

    def record_usage(self, user_id: str, model: str, input_tokens: int, output_tokens: int, context_id: str = None):
        """Record a usage event and update quota stats."""
        # Log event
        total = input_tokens + output_tokens
        log = UsageLog(
            user_id=user_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total,
            context_id=context_id
        )
        self.db.add(log)
        
        # Update Quota
        quota = self.get_or_create_quota(user_id)
        quota.requests_used += 1
        quota.tokens_used += total
        
        self.db.commit()

def get_usage_service(db: Session) -> UsageService:
    return UsageService(db)
