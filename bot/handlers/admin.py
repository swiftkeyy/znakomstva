"""Admin panel handler — superadmin, moderator, analyst roles."""
import structlog
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.config import settings

logger = structlog.get_logger(__name__)
router = Router(name="admin")

ROLES = {"superadmin": "👑 Главный админ", "moderator": "🛡 Модератор", "analyst": "📊 Аналитик"}


class AdminStates(StatesGroup):
    waiting_user_query = State()
    waiting_broadcast = State()
    waiting_role_id = State()
    waiting_role_type = State()


async def _get_role(telegram_id: int, session) -> str:
    admin_ids = settings.get_admin_ids()
    logger.info("admin_check", telegram_id=telegram_id, admin_ids=admin_ids)
    if telegram_id in admin_ids:
        return "superadmin"
    from database.repositories.admin_repository import AdminRepository
    return await AdminRepository(session).get_role(telegram_id) or ""


def _admin_menu_kb(role: str) -> InlineKeyboardMarkup:
    buttons = []
    if role in ("superadmin", "analyst"):
        buttons.append([InlineKeyboardButton(text="📊 Статистика", callback_data="adm:stats")])
    if role in ("superadmin", "moderator"):
        buttons.append([InlineKeyboardButton(text="✅ Верификации", callback_data="adm:verif")])
        buttons.append([InlineKeyboardButton(text="🚩 Жалобы", callback_data="adm:reports")])
    if role == "superadmin":
        buttons.append([InlineKeyboardButton(text="👤 Найти пользователя", callback_data="adm:find_user")])
        buttons.append([InlineKeyboardButton(text="📢 Рассылка", callback_data="adm:broadcast")])
        buttons.append([InlineKeyboardButton(text="👥 Управление ролями", callback_data="adm:roles")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("admin"))
async def cmd_admin(message: Message, user=None, session=None) -> None:
    if user is None:
        return
    role = await _get_role(message.from_user.id, session)
    if not role:
        await message.answer("⛔ Нет доступа.")
        return
    await message.answer(
        f"🔐 <b>Панель управления</b>\n\nРоль: {ROLES.get(role, role)}",
        parse_mode="HTML",
        reply_markup=_admin_menu_kb(role),
    )


@router.callback_query(F.data == "adm:stats")
async def adm_stats(callback: CallbackQuery, user=None, session=None) -> None:
    await callback.answer()
    role = await _get_role(callback.from_user.id, session)
    if not role:
        return
    try:
        from sqlalchemy import func, select
        from database.models.user import User
        from database.models.match import Match
        from database.models.message import Message as Msg
        from database.repositories.admin_repository import AdminRepository

        total_users = (await session.execute(select(func.count()).select_from(User))).scalar() or 0
        premium_users = (await session.execute(select(func.count()).where(User.is_premium.is_(True)))).scalar() or 0
        total_matches = (await session.execute(select(func.count()).select_from(Match))).scalar() or 0
        total_messages = (await session.execute(select(func.count()).select_from(Msg))).scalar() or 0
        admin_repo = AdminRepository(session)
        pending_verif = await admin_repo.count_pending_verifications()
        pending_reports = await admin_repo.count_pending_reports()

        await callback.message.edit_text(
            f"📊 <b>Статистика</b>\n\n"
            f"👥 Пользователей: {total_users}\n"
            f"💎 Premium: {premium_users}\n"
            f"❤️ Матчей: {total_matches}\n"
            f"💬 Сообщений: {total_messages}\n\n"
            f"⏳ Верификаций в очереди: {pending_verif}\n"
            f"🚩 Жалоб на рассмотрении: {pending_reports}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="adm:back")]]),
        )
    except Exception as e:
        logger.error("adm_stats_error", error=str(e))


@router.callback_query(F.data == "adm:verif")
async def adm_verif(callback: CallbackQuery, user=None, session=None) -> None:
    await callback.answer()
    role = await _get_role(callback.from_user.id, session)
    if role not in ("superadmin", "moderator"):
        return
    from database.repositories.admin_repository import AdminRepository
    items = await AdminRepository(session).get_pending_verifications(limit=1)
    if not items:
        await callback.message.edit_text("✅ Очередь верификаций пуста!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="adm:back")]]))
        return
    await _show_verification_item(callback.message, items[0], session)


async def _show_verification_item(message, item, session) -> None:
    from database.models.user import User
    from sqlalchemy import select
    user_result = await session.execute(select(User).where(User.id == item.user_id))
    target_user = user_result.scalar_one_or_none()
    name = target_user.first_name if target_user else f"ID {item.user_id}"
    level_names = {1: "⭕ Уровень 1", 2: "🎥 Уровень 2", 3: "🤖 Уровень 3"}
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"adm:verif_ok:{item.id}"), InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm:verif_no:{item.id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="adm:back")],
    ])
    caption = f"🔍 <b>Верификация #{item.id}</b>\n👤 {name}\n📋 {level_names.get(item.level, f'Уровень {item.level}')}"
    try:
        if item.media_type == "video":
            await message.answer_video(item.file_id, caption=caption, parse_mode="HTML", reply_markup=kb)
        else:
            await message.answer_photo(item.file_id, caption=caption, parse_mode="HTML", reply_markup=kb)
    except Exception:
        await message.answer(caption, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("adm:verif_ok:"))
async def adm_verif_approve(callback: CallbackQuery, user=None, session=None) -> None:
    await callback.answer("✅ Одобрено")
    item_id = int(callback.data.split(":")[2])
    from database.repositories.admin_repository import AdminRepository
    from sqlalchemy import update as sa_update
    from database.models.profile import Profile
    admin_repo = AdminRepository(session)
    item = await admin_repo.get_verification(item_id)
    if not item:
        return
    await admin_repo.resolve_verification(item_id, callback.from_user.id, "approved")
    await session.execute(sa_update(Profile).where(Profile.user_id == item.user_id).values(verification_level=item.level))
    await session.flush()
    try:
        await callback.bot.send_message(item.user_id, f"✅ <b>Верификация одобрена!</b>\n🏅 Уровень {item.level} получен.", parse_mode="HTML")
    except Exception:
        pass
    try:
        await callback.message.edit_caption(caption="✅ Одобрено", reply_markup=None)
    except Exception:
        pass
    items = await admin_repo.get_pending_verifications(limit=1)
    if items:
        await _show_verification_item(callback.message, items[0], session)
    else:
        await callback.message.answer("✅ Очередь верификаций пуста!")


@router.callback_query(F.data.startswith("adm:verif_no:"))
async def adm_verif_reject(callback: CallbackQuery, user=None, session=None) -> None:
    await callback.answer("❌ Отклонено")
    item_id = int(callback.data.split(":")[2])
    from database.repositories.admin_repository import AdminRepository
    admin_repo = AdminRepository(session)
    item = await admin_repo.get_verification(item_id)
    if not item:
        return
    await admin_repo.resolve_verification(item_id, callback.from_user.id, "rejected", "Не соответствует требованиям")
    try:
        await callback.bot.send_message(item.user_id, "❌ <b>Верификация отклонена.</b>\nПопробуй ещё раз.", parse_mode="HTML")
    except Exception:
        pass
    try:
        await callback.message.edit_caption(caption="❌ Отклонено", reply_markup=None)
    except Exception:
        pass
    items = await admin_repo.get_pending_verifications(limit=1)
    if items:
        await _show_verification_item(callback.message, items[0], session)
    else:
        await callback.message.answer("✅ Очередь верификаций пуста!")


@router.callback_query(F.data == "adm:reports")
async def adm_reports(callback: CallbackQuery, user=None, session=None) -> None:
    await callback.answer()
    role = await _get_role(callback.from_user.id, session)
    if role not in ("superadmin", "moderator"):
        return
    from database.repositories.admin_repository import AdminRepository
    reports = await AdminRepository(session).get_pending_reports(limit=1)
    if not reports:
        await callback.message.edit_text("✅ Жалоб нет!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="adm:back")]]))
        return
    await _show_report(callback.message, reports[0], session)


async def _show_report(message, report, session) -> None:
    from database.models.user import User
    from sqlalchemy import select
    reporter = (await session.execute(select(User).where(User.id == report.reporter_id))).scalar_one_or_none()
    reported = (await session.execute(select(User).where(User.id == report.reported_id))).scalar_one_or_none()
    text = (
        f"🚩 <b>Жалоба #{report.id}</b>\n\n"
        f"От: {reporter.first_name if reporter else report.reporter_id}\n"
        f"На: {reported.first_name if reported else report.reported_id}\n"
        f"Причина: {report.reason}"
        + (f"\nКомментарий: {report.comment}" if report.comment else "")
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔨 Забанить", callback_data=f"adm:rep_ban:{report.id}:{report.reported_id}"), InlineKeyboardButton(text="⚠️ Предупреждение", callback_data=f"adm:rep_warn:{report.id}:{report.reported_id}")],
        [InlineKeyboardButton(text="✅ Отклонить жалобу", callback_data=f"adm:rep_dismiss:{report.id}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="adm:back")],
    ])
    await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("adm:rep_ban:"))
async def adm_rep_ban(callback: CallbackQuery, user=None, session=None) -> None:
    await callback.answer("🔨 Забанен")
    parts = callback.data.split(":")
    report_id, reported_user_id = int(parts[2]), int(parts[3])
    from database.repositories.admin_repository import AdminRepository
    from database.repositories.user_repository import UserRepository
    from datetime import datetime, timedelta, timezone
    await AdminRepository(session).resolve_report(report_id, callback.from_user.id, "resolved")
    await UserRepository(session).suspend_user(reported_user_id, datetime.now(tz=timezone.utc) + timedelta(days=30))
    await session.flush()
    try:
        await callback.bot.send_message(reported_user_id, "🔨 Ваш аккаунт заблокирован на 30 дней.")
    except Exception:
        pass
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("✅ Пользователь забанен.")


@router.callback_query(F.data.startswith("adm:rep_warn:"))
async def adm_rep_warn(callback: CallbackQuery, user=None, session=None) -> None:
    await callback.answer("⚠️ Предупреждение")
    parts = callback.data.split(":")
    report_id, reported_user_id = int(parts[2]), int(parts[3])
    from database.repositories.admin_repository import AdminRepository
    from database.repositories.user_repository import UserRepository
    await AdminRepository(session).resolve_report(report_id, callback.from_user.id, "resolved")
    count = await UserRepository(session).add_warning(reported_user_id)
    await session.flush()
    try:
        await callback.bot.send_message(reported_user_id, f"⚠️ Предупреждение ({count}/3).")
    except Exception:
        pass
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"✅ Предупреждение выдано ({count}).")


@router.callback_query(F.data.startswith("adm:rep_dismiss:"))
async def adm_rep_dismiss(callback: CallbackQuery, user=None, session=None) -> None:
    await callback.answer()
    report_id = int(callback.data.split(":")[2])
    from database.repositories.admin_repository import AdminRepository
    await AdminRepository(session).resolve_report(report_id, callback.from_user.id, "dismissed")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("✅ Жалоба отклонена.")


@router.callback_query(F.data == "adm:find_user")
async def adm_find_user(callback: CallbackQuery, state: FSMContext, user=None, session=None) -> None:
    await callback.answer()
    if await _get_role(callback.from_user.id, session) != "superadmin":
        return
    await state.set_state(AdminStates.waiting_user_query)
    await callback.message.answer("👤 Введи Telegram ID или username:")


@router.message(AdminStates.waiting_user_query)
async def adm_find_user_input(message: Message, state: FSMContext, user=None, session=None) -> None:
    await state.clear()
    try:
        from database.models.user import User
        from sqlalchemy import select
        query = message.text.strip().lstrip("@")
        if query.isdigit():
            result = await session.execute(select(User).where(User.telegram_id == int(query)))
        else:
            result = await session.execute(select(User).where(User.username == query))
        target = result.scalar_one_or_none()
        if not target:
            await message.answer("❌ Пользователь не найден.")
            return
        status = "🔨 Забанен" if target.is_suspended else ("💎 Premium" if target.is_premium else "👤 Обычный")
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔨 Забанить 30д", callback_data=f"adm:ban:{target.id}"), InlineKeyboardButton(text="✅ Разбанить", callback_data=f"adm:unban:{target.id}")],
            [InlineKeyboardButton(text="💎 Выдать Premium", callback_data=f"adm:give_premium:{target.id}"), InlineKeyboardButton(text="⚠️ Предупреждение", callback_data=f"adm:warn:{target.id}")],
        ])
        await message.answer(
            f"👤 <b>{target.first_name}</b> (@{target.username or '—'})\nID: {target.telegram_id}\nСтатус: {status}\nПредупреждений: {target.warnings_count}\nКристаллов: {target.crystal_balance}",
            parse_mode="HTML", reply_markup=kb,
        )
    except Exception as e:
        logger.error("adm_find_user_error", error=str(e))
        await message.answer("Ошибка поиска.")


@router.callback_query(F.data.startswith("adm:ban:"))
async def adm_ban(callback: CallbackQuery, user=None, session=None) -> None:
    await callback.answer("🔨")
    target_id = int(callback.data.split(":")[2])
    from database.repositories.user_repository import UserRepository
    from datetime import datetime, timedelta, timezone
    await UserRepository(session).suspend_user(target_id, datetime.now(tz=timezone.utc) + timedelta(days=30))
    await session.flush()
    try:
        await callback.bot.send_message(target_id, "🔨 Ваш аккаунт заблокирован на 30 дней.")
    except Exception:
        pass
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("✅ Забанен.")


@router.callback_query(F.data.startswith("adm:unban:"))
async def adm_unban(callback: CallbackQuery, user=None, session=None) -> None:
    await callback.answer("✅")
    target_id = int(callback.data.split(":")[2])
    from sqlalchemy import update as sa_update
    from database.models.user import User
    await session.execute(sa_update(User).where(User.id == target_id).values(is_suspended=False, suspended_until=None))
    await session.flush()
    try:
        await callback.bot.send_message(target_id, "✅ Аккаунт разблокирован.")
    except Exception:
        pass
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("✅ Разбанен.")


@router.callback_query(F.data.startswith("adm:give_premium:"))
async def adm_give_premium(callback: CallbackQuery, user=None, session=None) -> None:
    await callback.answer("💎")
    target_id = int(callback.data.split(":")[2])
    from database.repositories.user_repository import UserRepository
    from datetime import datetime, timedelta, timezone
    await UserRepository(session).set_premium(target_id, datetime.now(tz=timezone.utc) + timedelta(days=30))
    await session.flush()
    try:
        await callback.bot.send_message(target_id, "💎 Вам выдан Premium на 30 дней!")
    except Exception:
        pass
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("✅ Premium выдан.")


@router.callback_query(F.data.startswith("adm:warn:"))
async def adm_warn(callback: CallbackQuery, user=None, session=None) -> None:
    await callback.answer("⚠️")
    target_id = int(callback.data.split(":")[2])
    from database.repositories.user_repository import UserRepository
    count = await UserRepository(session).add_warning(target_id)
    await session.flush()
    try:
        await callback.bot.send_message(target_id, f"⚠️ Предупреждение ({count}/3).")
    except Exception:
        pass
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"✅ Предупреждение выдано ({count}).")


@router.callback_query(F.data == "adm:broadcast")
async def adm_broadcast_start(callback: CallbackQuery, state: FSMContext, user=None, session=None) -> None:
    await callback.answer()
    if await _get_role(callback.from_user.id, session) != "superadmin":
        return
    await state.set_state(AdminStates.waiting_broadcast)
    await callback.message.answer("📢 Введи текст рассылки:")


@router.message(AdminStates.waiting_broadcast)
async def adm_broadcast_send(message: Message, state: FSMContext, user=None, session=None) -> None:
    await state.clear()
    text = message.text.strip()
    from database.models.user import User
    from sqlalchemy import select
    result = await session.execute(select(User).where(User.is_active.is_(True)))
    users = result.scalars().all()
    sent, failed = 0, 0
    for u in users:
        try:
            await message.bot.send_message(u.telegram_id, f"📢 {text}")
            sent += 1
        except Exception:
            failed += 1
    await message.answer(f"📢 Готово. Отправлено: {sent}, ошибок: {failed}")


@router.callback_query(F.data == "adm:roles")
async def adm_roles(callback: CallbackQuery, user=None, session=None) -> None:
    await callback.answer()
    if await _get_role(callback.from_user.id, session) != "superadmin":
        return
    from database.repositories.admin_repository import AdminRepository
    admins = await AdminRepository(session).list_admins()
    lines = "\n".join(f"• {ROLES.get(a.role, a.role)}: <code>{a.telegram_id}</code>" for a in admins) if admins else "Пока никого нет."
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Модератор", callback_data="adm:add_mod"), InlineKeyboardButton(text="➕ Аналитик", callback_data="adm:add_analyst")],
        [InlineKeyboardButton(text="➖ Снять роль", callback_data="adm:remove_role")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="adm:back")],
    ])
    await callback.message.edit_text(f"👥 <b>Администраторы</b>\n\n{lines}", parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.in_({"adm:add_mod", "adm:add_analyst", "adm:remove_role"}))
async def adm_role_action(callback: CallbackQuery, state: FSMContext, user=None, session=None) -> None:
    await callback.answer()
    action_map = {"adm:add_mod": "mod", "adm:add_analyst": "analyst", "adm:remove_role": "remove"}
    await state.set_state(AdminStates.waiting_role_id)
    await state.update_data(role_action=action_map[callback.data])
    prompts = {"mod": "Введи Telegram ID нового модератора:", "analyst": "Введи Telegram ID нового аналитика:", "remove": "Введи Telegram ID для снятия роли:"}
    await callback.message.answer(prompts[action_map[callback.data]])


@router.message(AdminStates.waiting_role_id)
async def adm_role_input(message: Message, state: FSMContext, user=None, session=None) -> None:
    fsm_data = await state.get_data()
    action = fsm_data.get("role_action")
    await state.clear()
    if not message.text.strip().isdigit():
        await message.answer("❌ Введи числовой Telegram ID.")
        return
    target_tg_id = int(message.text.strip())
    from database.repositories.admin_repository import AdminRepository
    admin_repo = AdminRepository(session)
    if action == "mod":
        await admin_repo.set_role(target_tg_id, "moderator", message.from_user.id)
        await message.answer(f"✅ {target_tg_id} назначен модератором.")
        try:
            await message.bot.send_message(target_tg_id, "🛡 Вам выдана роль <b>Модератор</b>. /admin", parse_mode="HTML")
        except Exception:
            pass
    elif action == "analyst":
        await admin_repo.set_role(target_tg_id, "analyst", message.from_user.id)
        await message.answer(f"✅ {target_tg_id} назначен аналитиком.")
    elif action == "remove":
        await admin_repo.remove_role(target_tg_id)
        await message.answer(f"✅ Роль снята с {target_tg_id}.")


@router.callback_query(F.data == "adm:back")
async def adm_back(callback: CallbackQuery, user=None, session=None) -> None:
    await callback.answer()
    role = await _get_role(callback.from_user.id, session)
    if not role:
        return
    await callback.message.edit_text(
        f"🔐 <b>Панель управления</b>\n\nРоль: {ROLES.get(role, role)}",
        parse_mode="HTML",
        reply_markup=_admin_menu_kb(role),
    )
