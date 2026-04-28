from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Enum, Float, ForeignKey, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

VerificationStatus = Enum("pending", "approved", "rejected", name="verification_status")


class VerificationAttempt(Base):
    __tablename__ = "verification_attempts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    level: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1, 2, or 3
    status: Mapped[str] = mapped_column(VerificationStatus, default="pending", nullable=False)
    file_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<VerificationAttempt id={self.id} user_id={self.user_id} level={self.level} status={self.status}>"
