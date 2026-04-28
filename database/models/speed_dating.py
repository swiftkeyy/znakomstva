from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, Integer, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

SessionStatus = Enum("scheduled", "active", "completed", "cancelled", name="speed_dating_status")


class SpeedDatingSession(Base):
    __tablename__ = "speed_dating_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(SmallInteger, default=3, nullable=False)
    status: Mapped[str] = mapped_column(SessionStatus, default="scheduled", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<SpeedDatingSession id={self.id} status={self.status}>"


class SpeedDatingParticipant(Base):
    __tablename__ = "speed_dating_participants"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("speed_dating_sessions.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<SpeedDatingParticipant id={self.id} session={self.session_id} user={self.user_id}>"


class SpeedDatingPair(Base):
    __tablename__ = "speed_dating_pairs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("speed_dating_sessions.id", ondelete="CASCADE"), nullable=False
    )
    user1_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user2_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    user1_wants_match: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    user2_wants_match: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    def __repr__(self) -> str:
        return f"<SpeedDatingPair id={self.id} session={self.session_id} u1={self.user1_id} u2={self.user2_id}>"
