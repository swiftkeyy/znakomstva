from typing import List, Optional

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.transaction import Transaction

from .base import BaseRepository

logger = structlog.get_logger(__name__)


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Transaction)

    async def create(
        self,
        user_id: int,
        transaction_type: str,
        amount: int,
        payment_method: Optional[str],
        status: str = "pending",
        metadata: Optional[str] = None,
    ) -> Transaction:
        tx = Transaction(
            user_id=user_id,
            transaction_type=transaction_type,
            amount=amount,
            payment_method=payment_method,
            status=status,
            metadata=metadata,
        )
        self.session.add(tx)
        await self.session.flush()
        await self.session.refresh(tx)
        logger.info(
            "transaction_created",
            user_id=user_id,
            type=transaction_type,
            amount=amount,
            status=status,
        )
        return tx

    async def get_user_transactions(
        self, user_id: int, limit: int = 50
    ) -> List[Transaction]:
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(self, transaction_id: int, status: str) -> None:
        await self.session.execute(
            update(Transaction)
            .where(Transaction.id == transaction_id)
            .values(status=status)
        )
        await self.session.flush()
        logger.info("transaction_status_updated", transaction_id=transaction_id, status=status)
