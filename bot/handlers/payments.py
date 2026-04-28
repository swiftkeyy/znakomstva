"""Payments handler — pre-checkout and successful payment processing."""
import structlog
from aiogram import Router
from aiogram.types import Message, PreCheckoutQuery

logger = structlog.get_logger(__name__)
router = Router(name="payments")


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    await query.answer(ok=True)
    logger.info("pre_checkout_approved", user_id=query.from_user.id, payload=query.invoice_payload)


@router.message(lambda m: m.successful_payment is not None)
async def successful_payment(message: Message, user=None, session=None) -> None:
    if user is None:
        return
    payment = message.successful_payment
    try:
        from bot.services.payment_service import PaymentService
        from database.repositories.user_repository import UserRepository
        from database.repositories.transaction_repository import TransactionRepository

        success = await PaymentService(UserRepository(session), TransactionRepository(session)).process_payment(
            user_id=user.id, payload=payment.invoice_payload,
            amount=payment.total_amount, method=payment.provider_payment_charge_id or "telegram",
        )
        if success:
            payload = payment.invoice_payload
            if payload.startswith("premium:"):
                months = int(payload.split(":")[2])
                await message.answer(f"🎉 <b>Premium активирован на {months} мес.!</b>", parse_mode="HTML")
            elif payload.startswith("crystals:"):
                crystals = int(payload.split(":")[2])
                await message.answer(f"💠 <b>+{crystals} кристаллов</b> добавлено!", parse_mode="HTML")
            else:
                await message.answer("✅ Оплата прошла успешно!")
        else:
            await message.answer("⚠️ Оплата получена, но возникла ошибка при активации. Обратись в поддержку.")
    except Exception as e:
        logger.error("successful_payment_error", user_id=user.id, error=str(e))
        await message.answer("⚠️ Оплата получена, но возникла ошибка при обработке. Обратись в поддержку.")


