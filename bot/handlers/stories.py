"""Stories handler — view, upload, and delete user stories."""
import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.keyboards import StoryCallback

logger = structlog.get_logger(__name__)
router = Router(name="stories")

_STORY_UPLOAD_STATE = "story_upload"


@router.message(F.text == "📖 Мои истории")
async def show_stories(message: Message, data: dict) -> None:
    user = data["user"]
    session = data["session"]

    try:
        from bot.services.story_service import StoryService
        from database.repositories.story_repository import StoryRepository

        story_service = StoryService(StoryRepository(session))
        stories = await story_service.get_user_stories(user.id)

        if not stories:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить историю", callback_data="story:upload")]
            ])
            await message.answer(
                "📖 У тебя пока нет активных историй.\n"
                "Истории живут 24 часа.",
                reply_markup=kb,
            )
            return

        buttons = []
        for s in stories:
            buttons.append([
                InlineKeyboardButton(
                    text=f"👁 {s.view_count} просм. | {s.media_type}",
                    callback_data=StoryCallback(action="view", story_id=s.id).pack(),
                ),
                InlineKeyboardButton(
                    text="🗑",
                    callback_data=StoryCallback(action="delete", story_id=s.id).pack(),
                ),
            ])
        buttons.append([InlineKeyboardButton(text="➕ Добавить историю", callback_data="story:upload")])

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(
            f"📖 <b>Мои истории</b> ({len(stories)} активных):",
            parse_mode="HTML",
            reply_markup=kb,
        )
        logger.info("stories_shown", user_id=user.id, count=len(stories))
    except Exception as e:
        logger.error("show_stories_error", user_id=user.id, error=str(e))
        await message.answer("Не удалось загрузить истории. Попробуй позже.")


@router.callback_query(F.data == "story:upload")
async def story_upload_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.update_data(awaiting_story=True)
    await callback.message.answer(
        "📸 Отправь фото или видео для истории.\n"
        "История будет активна 24 часа."
    )


@router.message(F.photo)
async def story_upload_photo(message: Message, state: FSMContext, data: dict) -> None:
    fsm_data = await state.get_data()
    if not fsm_data.get("awaiting_story"):
        return  # Not in story upload mode

    user = data["user"]
    session = data["session"]

    try:
        from bot.services.story_service import StoryService
        from database.repositories.story_repository import StoryRepository

        story_service = StoryService(StoryRepository(session))
        file_id = message.photo[-1].file_id
        success, msg = await story_service.create_story(user.id, file_id, "photo", user.is_premium)

        await state.update_data(awaiting_story=False)
        await message.answer(f"{'✅' if success else '❌'} {msg}")
        logger.info("story_photo_uploaded", user_id=user.id, success=success)
    except Exception as e:
        logger.error("story_upload_photo_error", user_id=user.id, error=str(e))
        await message.answer("Ошибка при загрузке истории. Попробуй позже.")


@router.message(F.video)
async def story_upload_video(message: Message, state: FSMContext, data: dict) -> None:
    fsm_data = await state.get_data()
    if not fsm_data.get("awaiting_story"):
        return  # Not in story upload mode

    user = data["user"]
    session = data["session"]

    try:
        from bot.services.story_service import StoryService
        from database.repositories.story_repository import StoryRepository

        story_service = StoryService(StoryRepository(session))
        file_id = message.video.file_id
        success, msg = await story_service.create_story(user.id, file_id, "video", user.is_premium)

        await state.update_data(awaiting_story=False)
        await message.answer(f"{'✅' if success else '❌'} {msg}")
        logger.info("story_video_uploaded", user_id=user.id, success=success)
    except Exception as e:
        logger.error("story_upload_video_error", user_id=user.id, error=str(e))
        await message.answer("Ошибка при загрузке истории. Попробуй позже.")


@router.callback_query(StoryCallback.filter(F.action == "view"))
async def story_view(callback: CallbackQuery, callback_data: StoryCallback, data: dict) -> None:
    await callback.answer()
    user = data["user"]
    session = data["session"]

    try:
        from bot.services.story_service import StoryService
        from database.repositories.story_repository import StoryRepository

        story_service = StoryService(StoryRepository(session))
        story = await story_service.view_story(callback_data.story_id, user.id)

        if story.media_type == "photo":
            await callback.message.answer_photo(
                story.file_id,
                caption=f"👁 Просмотров: {story.view_count}",
            )
        elif story.media_type == "video":
            await callback.message.answer_video(
                story.file_id,
                caption=f"👁 Просмотров: {story.view_count}",
            )
        logger.info("story_viewed", user_id=user.id, story_id=callback_data.story_id)
    except ValueError:
        await callback.message.answer("История не найдена или уже удалена.")
    except Exception as e:
        logger.error("story_view_error", user_id=user.id, error=str(e))
        await callback.message.answer("Не удалось загрузить историю. Попробуй позже.")


@router.callback_query(StoryCallback.filter(F.action == "delete"))
async def story_delete(callback: CallbackQuery, callback_data: StoryCallback, data: dict) -> None:
    await callback.answer()
    user = data["user"]
    session = data["session"]

    try:
        from database.repositories.story_repository import StoryRepository
        story_repo = StoryRepository(session)
        story = await story_repo.get_by_id(callback_data.story_id)

        if story is None or story.user_id != user.id:
            await callback.message.answer("История не найдена.")
            return

        await story_repo.delete(callback_data.story_id)
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer("🗑 История удалена.")
        logger.info("story_deleted", user_id=user.id, story_id=callback_data.story_id)
    except Exception as e:
        logger.error("story_delete_error", user_id=user.id, error=str(e))
        await callback.message.answer("Не удалось удалить историю. Попробуй позже.")
