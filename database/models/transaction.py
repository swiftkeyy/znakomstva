from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User

TransactionType = Enum("premium", "crystals", "boost", name="transaction_type")
PaymentMethod = Enum("telegram_stars", "yukassa", name="payment_method")
TransactionStatus = Enum("pending", "completed", "failed", name="transaction_status")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    transaction_type: Mapped[str] = mapped_column(TransactionType, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_method: Mapped[Optional[str]] = mapped_column(PaymentMethod, nullable=True)
    status: Mapped[str] = mapped_column(TransactionStatus, default="pending", nullable=False)
    transaction_metadata: Mapped[Optional[str]] = mapped_column("metadata", Text, nullable=True)  # JSON text
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction id={self.id} user_id={self.user_id} type={self.transaction_type} status={self.status}>"
