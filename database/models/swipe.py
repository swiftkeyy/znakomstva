from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

SwipeAction = Enum("like", "pass", "super_like", name="swipe_action")


class Swipe(Base):
    __tablename__ = "swipes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    target_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(SwipeAction, nullable=False)
    is_super_swipe: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_swipes_user_target", "user_id", "target_user_id"),
    )

    def __repr__(self) -> str:
        return f"<Swipe id={self.id} user_id={self.user_id} target={self.target_user_id} action={self.action}>"
