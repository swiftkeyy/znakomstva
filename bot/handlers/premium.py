"""Premium handler — subscriptions and crystal packages."""
import structlog
from aiogram import F, Router
from aiogram.types import CallbackQuery, LabeledPrice, Message

from bot.keyboards import PremiumCallback, main_menu_keyboard, premium_keyboard

logger = structlog.get_logger(__name__)
router = Router(name="premium")

_PREMIUM_MONTHS = {"sub_1": 1, "sub_3": 3, "sub_12": 12}
_CRYSTAL_AMOUNTS = {
    "crystals_100": 100,
    "crystals_500": 500,
    "crystals_1000": 1000,
    "crystals_5000": 5000,
}


@router.message(F.text == "💎 Бусты и кристаллы")
async def show_premium(message: Message, user=None, session=None) -> None:
        status = "✅ Premium активен" if user.is_premium else "❌ Premium не активен"
    await message.answer(
        f"💎 <b>Бусты и кристаллы</b>\n\n"
        f"Статус: {status}\n"
        f"💠 Кристаллов: {user.crystals}\n\n"
        "Выбери пакет:",
        parse_mode="HTML",
        reply_markup=premium_keyboard(),
    )
    logger.info("premium_menu_shown", user_id=user.id)


@router.callback_query(PremiumCallback.filter())
async def premium_callback(callback: CallbackQuery, callback_data: PremiumCallback, user=None, session=None) -> None:
    await callback.answer()
        action = callback_data.action

    try:
        from bot.services.payment_service import PaymentService
        from database.repositories.user_repository import UserRepository
        from database.repositories.transaction_repository import TransactionRepository
        from bot.config import settings as cfg

                payment_service = PaymentService(
            UserRepository(session),
            TransactionRepository(session),
        )

        if action in _PREMIUM_MONTHS:
            months = _PREMIUM_MONTHS[action]
            invoice = payment_service.get_premium_invoice(user.id, months)
        elif action in _CRYSTAL_AMOUNTS:
            amount = _CRYSTAL_AMOUNTS[action]
            invoice = payment_service.get_crystals_invoice(user.id, amount)
        else:
            await callback.message.answer("Неизвестный пакет.")
            return

        prices = [LabeledPrice(label=p["label"], amount=p["amount"]) for p in invoice["prices"]]
        await callback.message.answer_invoice(
            title=invoice["title"],
            description=invoice["description"],
            payload=invoice["payload"],
            provider_token=cfg.telegram_payment_token,
            currency=invoice["currency"],
            prices=prices,
        )
        logger.info("invoice_sent", user_id=user.id, action=action)
    except Exception as e:
        logger.error("premium_callback_error", user_id=user.id, action=action, error=str(e))
        await callback.message.answer("Не удалось создать счёт. Попробуй позже.")



