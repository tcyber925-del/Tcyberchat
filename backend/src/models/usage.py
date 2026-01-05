from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from ..database import Base

class UsageLog(Base):
    """Log of individual LLM usage events"""
    __tablename__ = "usage_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    model = Column(String(100), nullable=False)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    # Optional context (e.g. conversation_id)
    context_id = Column(String(36), nullable=True)

class UserQuota(Base):
    """Quota limits and current usage for a user"""
    __tablename__ = "user_quotas"

    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    
    # Tier name (free, pro, enterprise)
    tier = Column(String(50), default="free")
    
    # Limits (0 = unlimited)
    daily_request_limit = Column(Integer, default=50)
    daily_token_limit = Column(Integer, default=10000)
    
    # Reset tracking
    last_reset_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Current Usage (since last reset)
    requests_used = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)
    
    user = relationship("User", backref="quota")
