"""Payment service — Telegram Stars only."""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import structlog

from database.repositories.transaction_repository import TransactionRepository
from database.repositories.user_repository import UserRepository

logger = structlog.get_logger(__name__)

# Prices in Telegram Stars (XTR)
CRYSTAL_PACKAGES: Dict[int, int] = {
    100: 25,
    500: 99,
    1000: 179,
    5000: 749,
}

PREMIUM_PACKAGES: Dict[int, int] = {
    1: 75,
    3: 179,
    12: 499,
}


class PaymentService:
    def __init__(self, user_repo: UserRepository, transaction_repo: TransactionRepository) -> None:
        self.user_repo = user_repo
        self.transaction_repo = transaction_repo

    def get_premium_invoice(self, user_id: int, months: int) -> Dict[str, Any]:
        price = PREMIUM_PACKAGES.get(months)
        if price is None:
            raise ValueError(f"Неверный период: {months} мес.")
        return {
            "title": f"⭐ Premium {months} мес.",
            "description": f"Подписка Premium на {months} мес. Безлимитные свайпы и приоритет в поиске.",
            "payload": f"premium:{user_id}:{months}",
            "currency": "XTR",
            "prices": [{"label": f"Premium {months} мес.", "amount": price}],
        }

    def get_crystals_invoice(self, user_id: int, amount: int) -> Dict[str, Any]:
        price = CRYSTAL_PACKAGES.get(amount)
        if price is None:
            raise ValueError(f"Неверное количество: {amount}")
        return {
            "title": f"💠 {amount} кристаллов",
            "description": f"Пополнение баланса на {amount} кристаллов.",
            "payload": f"crystals:{user_id}:{amount}",
            "currency": "XTR",
            "prices": [{"label": f"{amount} кристаллов", "amount": price}],
        }

    async def process_payment(self, user_id: int, payload: str, amount: int, method: str) -> bool:
        try:
            parts = payload.split(":")
            if len(parts) < 3:
                logger.error("invalid_payment_payload", payload=payload)
                return False

            payment_type = parts[0]

            if payment_type == "premium":
                months = int(parts[2])
                expires_at = datetime.now(tz=timezone.utc) + timedelta(days=30 * months)
                await self.user_repo.set_premium(user_id, expires_at)
                logger.info("premium_activated", user_id=user_id, months=months)
            elif payment_type == "crystals":
                crystals = int(parts[2])
                await self.user_repo.add_crystals(user_id, crystals)
                logger.info("crystals_added_payment", user_id=user_id, crystals=crystals)
            else:
                return False

            return True
        except Exception as e:
            logger.error("process_payment_error", user_id=user_id, payload=payload, error=str(e))
            return False
