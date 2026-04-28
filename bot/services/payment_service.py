"""Payment service — premium subscriptions and crystal packages."""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import structlog

from database.repositories.transaction_repository import TransactionRepository
from database.repositories.user_repository import UserRepository

logger = structlog.get_logger(__name__)

# Crystal packages: {amount: price_rub}
CRYSTAL_PACKAGES: Dict[int, int] = {
    100: 99,
    500: 399,
    1000: 699,
    5000: 2999,
}

# Premium packages: {months: price_rub}
PREMIUM_PACKAGES: Dict[int, int] = {
    1: 299,
    3: 699,
    12: 1999,
}


class PaymentService:
    def __init__(
        self,
        user_repo: UserRepository,
        transaction_repo: TransactionRepository,
    ) -> None:
        self.user_repo = user_repo
        self.transaction_repo = transaction_repo

    def get_premium_invoice(self, user_id: int, months: int) -> Dict[str, Any]:
        """Return invoice data dict for aiogram send_invoice."""
        price = PREMIUM_PACKAGES.get(months)
        if price is None:
            raise ValueError(f"Неверный период подписки: {months} мес.")
        return {
            "title": f"Premium {months} мес.",
            "description": f"Подписка Premium на {months} месяц(ев). Безлимитные свайпы, приоритет в поиске и многое другое.",
            "payload": f"premium:{user_id}:{months}",
            "currency": "RUB",
            "prices": [{"label": f"Premium {months} мес.", "amount": price * 100}],
        }

    def get_crystals_invoice(self, user_id: int, amount: int) -> Dict[str, Any]:
        """Return invoice data dict for aiogram send_invoice."""
        price = CRYSTAL_PACKAGES.get(amount)
        if price is None:
            raise ValueError(f"Неверное количество кристаллов: {amount}")
        return {
            "title": f"{amount} кристаллов",
            "description": f"Пополнение баланса на {amount} кристаллов для использования в приложении.",
            "payload": f"crystals:{user_id}:{amount}",
            "currency": "RUB",
            "prices": [{"label": f"{amount} кристаллов", "amount": price * 100}],
        }

    async def process_payment(
        self, user_id: int, payload: str, amount: int, method: str
    ) -> bool:
        """Parse payload and activate premium or add crystals. Returns True on success."""
        try:
            parts = payload.split(":")
            if len(parts) < 3:
                logger.error("invalid_payment_payload", payload=payload)
                return False

            payment_type = parts[0]

            await self.transaction_repo.create(
                user_id=user_id,
                transaction_type=payment_type if payment_type in ("premium", "crystals") else "crystals",
                amount=amount,
                payment_method=method,
                status="pending",
                metadata=payload,
            )

            if payment_type == "premium":
                months = int(parts[2])
                expires_at = datetime.now(tz=timezone.utc) + timedelta(days=30 * months)
                await self.user_repo.set_premium(user_id, expires_at)
                logger.info("premium_activated", user_id=user_id, months=months, expires_at=expires_at)

            elif payment_type == "crystals":
                crystals = int(parts[2])
                await self.user_repo.add_crystals(user_id, crystals)
                logger.info("crystals_added_payment", user_id=user_id, crystals=crystals)

            else:
                logger.error("unknown_payment_type", payload=payload)
                return False

            # Mark latest transaction as completed
            txs = await self.transaction_repo.get_user_transactions(user_id, limit=1)
            if txs:
                await self.transaction_repo.update_status(txs[0].id, "completed")

            return True

        except Exception as e:
            logger.error("process_payment_error", user_id=user_id, payload=payload, error=str(e))
            return False
