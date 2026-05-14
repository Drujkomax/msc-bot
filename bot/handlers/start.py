from __future__ import annotations

import re
from typing import Union

from aiogram.types import CallbackQuery, Message

from ..auth import can_start_visit, get_profile_by_telegram_id, login_and_link
from ..i18n import norm_lang, t
from ..keyboards import main_menu
from ..session import clear_session, get_session, set_session

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


async def handle_start(event: Union[Message, CallbackQuery]) -> None:
    tg_id = event.from_user.id if event.from_user else None
    if tg_id is None:
        return
    message = event if isinstance(event, Message) else event.message
    if message is None:
        return

    existing = get_profile_by_telegram_id(tg_id)
    if existing:
        lang = norm_lang(existing.language)
        if not can_start_visit(existing.role):
            await message.answer(t(lang, "login_role_denied"))
            return
        clear_session(tg_id)
        set_session(tg_id, "main_menu")
        await message.answer(
            t(lang, "main_menu_title", name=existing.full_name or existing.email or ""),
            reply_markup=main_menu(lang),
        )
        return

    set_session(tg_id, "awaiting_email")
    await message.answer(t("ru", "unlinked_prompt"))


async def handle_auth_flow(message: Message, text: str) -> bool:
    """Return True if the message was consumed by the auth flow."""
    tg_id = message.from_user.id if message.from_user else None
    if tg_id is None:
        return False
    session = get_session(tg_id)
    if not session:
        return False

    if session.state == "awaiting_email":
        if not EMAIL_RE.match(text):
            await message.answer(t("ru", "unlinked_prompt"))
            return True
        set_session(tg_id, "awaiting_password", {"email": text.strip().lower()})
        await message.answer(t("ru", "login_password_prompt"))
        return True

    if session.state == "awaiting_password":
        email = (session.context or {}).get("email") or ""
        # best-effort: delete the password message for hygiene
        try:
            await message.delete()
        except Exception:  # noqa: BLE001
            pass

        username = message.from_user.username if message.from_user else None
        linked = login_and_link(email, text, tg_id, username)
        if not linked:
            set_session(tg_id, "awaiting_email")
            await message.answer(t("ru", "login_invalid"))
            return True
        lang = norm_lang(linked.language)
        if not can_start_visit(linked.role):
            clear_session(tg_id)
            await message.answer(t(lang, "login_role_denied"))
            return True
        set_session(tg_id, "main_menu")
        name = linked.full_name or linked.email or ""
        await message.answer(t(lang, "linked_success", name=name))
        await message.answer(
            t(lang, "main_menu_title", name=name),
            reply_markup=main_menu(lang),
        )
        return True

    return False
