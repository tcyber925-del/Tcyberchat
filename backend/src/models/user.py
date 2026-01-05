from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship

from ..database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    provider = Column(String, default="local")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    # Verification token relationship
    verification_token = relationship("EmailVerification", back_populates="user", uselist=False, cascade="all, delete-orphan")

class EmailVerification(Base):
    __tablename__ = "email_verifications"

    token = Column(String, primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"))
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="verification_token")
