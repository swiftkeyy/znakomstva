"""Admin roles and reports models."""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AdminRole(Base):
    __tablename__ = "admin_roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)  # superadmin, moderator, analyst
    granted_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    reporter_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reported_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reason: Mapped[str] = mapped_column(String(64), nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)  # pending, resolved, dismissed
    resolved_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VerificationQueue(Base):
    __tablename__ = "verification_queue"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    level: Mapped[int] = mapped_column(nullable=False)  # 1, 2, 3
    file_id: Mapped[str] = mapped_column(String(256), nullable=False)
    media_type: Mapped[str] = mapped_column(String(16), default="photo")  # photo, video
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending, approved, rejected
    reviewed_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    reject_reason: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
