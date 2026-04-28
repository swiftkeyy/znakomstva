"""Payments handler — pre-checkout and successful payment processing."""
import structlog
from aiogram import Router
from aiogram.types import Message, PreCheckoutQuery

logger = structlog.get_logger(__name__)
router = Router(name="payments")


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    """Always approve pre-checkout queries."""
    await query.answer(ok=True)
    logger.info("pre_checkout_approved", user_id=query.from_user.id, payload=query.invoice_payload)


@router.message(lambda m: m.successful_payment is not None)
async def successful_payment(message: Message, data: dict) -> None:
    user = data["user"]
    session = data["session"]
    payment = message.successful_payment

    try:
        from bot.services.payment_service import PaymentService
        from database.repositories.user_repository import UserRepository
        from database.repositories.transaction_repository import TransactionRepository

        payment_service = PaymentService(
            UserRepository(session),
            TransactionRepository(session),
        )

        success = await payment_service.process_payment(
            user_id=user.id,
            payload=payment.invoice_payload,
            amount=payment.total_amount,
            method=payment.provider_payment_charge_id or "telegram",
        )

        if success:
            payload = payment.invoice_payload
            if payload.startswith("premium:"):
                months = int(payload.split(":")[2])
                await message.answer(
                    f"🎉 <b>Premium активирован на {months} мес.!</b>\n\n"
                    "Наслаждайся безлимитными свайпами и приоритетом в поиске.",
                    parse_mode="HTML",
                )
            elif payload.startswith("crystals:"):
                crystals = int(payload.split(":")[2])
                await message.answer(
                    f"💠 <b>+{crystals} кристаллов</b> добавлено на твой счёт!",
                    parse_mode="HTML",
                )
            else:
                await message.answer("✅ Оплата прошла успешно!")
        else:
            await message.answer(
                "⚠️ Оплата получена, но возникла ошибка при активации.\n"
                "Обратись в поддержку."
            )

        logger.info(
            "payment_processed",
            user_id=user.id,
            payload=payment.invoice_payload,
            amount=payment.total_amount,
            success=success,
        )
    except Exception as e:
        logger.error("successful_payment_error", user_id=user.id, error=str(e))
        await message.answer(
            "⚠️ Оплата получена, но возникла ошибка при обработке.\n"
            "Обратись в поддержку."
        )
