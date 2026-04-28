"""Premium handler — subscriptions and crystal packages."""
import structlog
from aiogram import F, Router
from aiogram.types import CallbackQuery, LabeledPrice, Message

from bot.keyboards import PremiumCallback, main_menu_keyboard, premium_keyboard

logger = structlog.get_logger(__name__)
router = Router(name="premium")

_PREMIUM_MONTHS = {"sub_1": 1, "sub_3": 3, "sub_12": 12}
_CRYSTAL_AMOUNTS = {"crystals_100": 100, "crystals_500": 500, "crystals_1000": 1000, "crystals_5000": 5000}


@router.message(F.text == "💎 Бусты и кристаллы")
async def show_premium(message: Message, user=None, session=None) -> None:
    if user is None:
        return
    status = "✅ Premium активен" if user.is_premium else "❌ Premium не активен"
    await message.answer(
        f"💎 <b>Бусты и кристаллы</b>\n\nСтатус: {status}\n💠 Кристаллов: {user.crystals}\n\nВыбери пакет:",
        parse_mode="HTML", reply_markup=premium_keyboard(),
    )


@router.callback_query(PremiumCallback.filter())
async def premium_callback(callback: CallbackQuery, callback_data: PremiumCallback, user=None, session=None) -> None:
    await callback.answer()
    if user is None:
        return
    action = callback_data.action
    try:
        from bot.services.payment_service import PaymentService
        from database.repositories.user_repository import UserRepository
        from database.repositories.transaction_repository import TransactionRepository
        from bot.config import settings as cfg

        if not cfg.telegram_payment_token:
            await callback.message.answer("💳 Платежи временно недоступны. Обратись к администратору.")
            return

        payment_service = PaymentService(UserRepository(session), TransactionRepository(session))

        if action in _PREMIUM_MONTHS:
            invoice = payment_service.get_premium_invoice(user.id, _PREMIUM_MONTHS[action])
        elif action in _CRYSTAL_AMOUNTS:
            invoice = payment_service.get_crystals_invoice(user.id, _CRYSTAL_AMOUNTS[action])
        else:
            await callback.message.answer("Неизвестный пакет.")
            return

        prices = [LabeledPrice(label=p["label"], amount=p["amount"]) for p in invoice["prices"]]
        await callback.message.answer_invoice(
            title=invoice["title"], description=invoice["description"],
            payload=invoice["payload"], provider_token=cfg.telegram_payment_token,
            currency=invoice["currency"], prices=prices,
        )
    except Exception as e:
        logger.error("premium_callback_error", user_id=user.id, action=action, error=str(e))
        await callback.message.answer("Не удалось создать счёт. Попробуй позже.")
