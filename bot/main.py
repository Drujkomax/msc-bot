from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import CommandStart, Command
from aiogram.types import CallbackQuery, Message

from .auth import can_start_visit, get_profile_by_telegram_id
from .config import settings
from .handlers.history import show_history
from .handlers.language import toggle_language
from .handlers.main_menu import show_main_menu
from .handlers.stages import (
    enter_arrival,
    enter_briefing,
    enter_completion,
    enter_specialist,
    handle_briefing_category_pick,
    handle_outcome_pick,
    handle_specialist_pick,
    handle_stage_done,
    handle_stage_photo,
    handle_stage_skip,
    handle_stage_text,
)
from .handlers.start import handle_auth_flow, handle_start
from .handlers.visit_actions import (
    ask_cancel_visit,
    confirm_cancel_visit,
    finish_visit_from_menu,
)
from .handlers.visit_start import (
    capture_new_clinic_address_or_skip,
    capture_new_clinic_name,
    handle_clinic_search,
    open_visit_menu,
    pick_existing_clinic,
    prompt_new_clinic_name,
    start_new_visit_flow,
)
from .i18n import norm_lang, t
from .session import get_session

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("msc-bot")

dp = Dispatcher()


# ============== Commands ==============

@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await handle_start(message)


@dp.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    tg_id = message.from_user.id if message.from_user else None
    if tg_id is None:
        return
    profile = get_profile_by_telegram_id(tg_id)
    if not profile:
        await handle_start(message)
        return
    await show_main_menu(message, profile)


# ============== Callback queries ==============

@dp.callback_query(F.data)
async def on_callback(event: CallbackQuery) -> None:
    data = event.data
    tg_id = event.from_user.id if event.from_user else None
    if tg_id is None or data is None:
        return
    try:
        await event.answer()
    except TelegramAPIError:
        pass

    profile = get_profile_by_telegram_id(tg_id)
    if not profile:
        await handle_start(event)
        return

    lang = norm_lang(profile.language)
    if not can_start_visit(profile.role):
        if event.message:
            await event.message.answer(t(lang, "unlinked_role_denied"))
        return

    if data == "menu:main":
        await show_main_menu(event, profile)
        return
    if data == "lang:toggle":
        await toggle_language(event, profile)
        return

    if data == "visit:start":
        await start_new_visit_flow(event, profile)
        return
    if data == "visit:history":
        await show_history(event, profile)
        return
    if data == "visit:menu":
        session = get_session(tg_id)
        vid = (session.context if session else {}).get("visit_id")
        if vid:
            await open_visit_menu(event, profile, vid)
        else:
            await show_main_menu(event, profile)
        return
    if data == "visit:cancel":
        await ask_cancel_visit(event, profile)
        return
    if data == "visit:cancel_confirm":
        await confirm_cancel_visit(event, profile)
        return
    if data == "visit:cancel_pick":
        await show_main_menu(event, profile)
        return
    if data == "visit:finish":
        await finish_visit_from_menu(event, profile)
        return

    if data.startswith("clinic:pick:"):
        client_id = data[len("clinic:pick:") :]
        await pick_existing_clinic(event, profile, client_id)
        return
    if data == "clinic:new":
        await prompt_new_clinic_name(event, profile)
        return

    if data == "stage:arrival":
        await enter_arrival(event, profile)
        return
    if data == "stage:specialist":
        await enter_specialist(event, profile)
        return
    if data == "stage:briefing":
        await enter_briefing(event, profile)
        return
    if data == "stage:completion":
        await enter_completion(event, profile)
        return
    if data == "stage:done":
        await handle_stage_done(event, profile)
        return
    if data == "stage:skip":
        await handle_stage_skip(event, profile)
        return

    if data.startswith("outcome:"):
        outcome = data[len("outcome:") :]
        await handle_outcome_pick(event, profile, outcome)
        return

    if data.startswith("bc:"):
        category = data[len("bc:") :]
        await handle_briefing_category_pick(event, profile, category)
        return

    if data.startswith(("eq:", "bg:", "tl:", "lq:")):
        idx = data.index(":")
        prefix = data[:idx]
        value = data[idx + 1 :]
        await handle_specialist_pick(event, profile, prefix, value)
        return


# ============== Photo messages ==============

@dp.message(F.photo)
async def on_photo(message: Message) -> None:
    tg_id = message.from_user.id if message.from_user else None
    if tg_id is None or not message.photo:
        return
    profile = get_profile_by_telegram_id(tg_id)
    if not profile:
        return
    session = get_session(tg_id)
    if not session:
        return
    largest = message.photo[-1]
    await handle_stage_photo(message, profile, session.state, largest.file_id)


# ============== Text messages ==============

@dp.message(F.text)
async def on_text(message: Message) -> None:
    tg_id = message.from_user.id if message.from_user else None
    if tg_id is None or not message.text:
        return
    text = message.text.strip()

    profile = get_profile_by_telegram_id(tg_id)
    if not profile:
        handled = await handle_auth_flow(message, text)
        if not handled:
            await handle_start(message)
        return

    lang = norm_lang(profile.language)
    if not can_start_visit(profile.role):
        await message.answer(t(lang, "unlinked_role_denied"))
        return

    session = get_session(tg_id)
    state = session.state if session else "main_menu"

    if state == "picking_clinic":
        await handle_clinic_search(message, profile, text)
        return
    if state == "new_clinic_name":
        await capture_new_clinic_name(message, profile, text)
        return
    if state == "new_clinic_address":
        await capture_new_clinic_address_or_skip(message, profile, text)
        return

    if state.startswith("stage:"):
        handled = await handle_stage_text(message, profile, state, text)
        if handled:
            return

    await message.answer(t(lang, "unknown_input"))
    await show_main_menu(message, profile)


# ============== Errors ==============

@dp.errors()
async def on_error(event) -> bool:  # type: ignore[no-untyped-def]
    log.exception("Update handling failed: %s", event.exception)
    return True


# ============== Boot ==============

async def main() -> None:
    log.info("MSC Visits Bot starting…")
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    me = await bot.get_me()
    log.info("Bot @%s is up.", me.username)
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
