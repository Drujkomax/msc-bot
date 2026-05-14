from __future__ import annotations

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from ..i18n import norm_lang, t
from ..keyboards import main_menu
from ..session import set_session
from ..types import Profile


async def show_main_menu(event: Message | CallbackQuery, profile: Profile) -> None:
    lang = norm_lang(profile.language)
    tg_id = event.from_user.id if event.from_user else None
    if tg_id is None:
        return
    set_session(tg_id, "main_menu")
    text = t(lang, "main_menu_title", name=profile.full_name or profile.email or "")
    kb = main_menu(lang)

    if isinstance(event, CallbackQuery) and event.message:
        try:
            await event.message.edit_text(text, reply_markup=kb)
            return
        except TelegramBadRequest:
            # fall through to a fresh message
            pass
        target_message = event.message
    else:
        target_message = event if isinstance(event, Message) else event.message  # type: ignore[assignment]

    if target_message:
        await target_message.answer(text, reply_markup=kb)
