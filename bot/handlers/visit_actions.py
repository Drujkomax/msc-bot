from __future__ import annotations

from aiogram.types import CallbackQuery

from ..i18n import norm_lang, t
from ..keyboards import confirm_cancel
from ..session import clear_session
from ..types import Profile
from ..visits import (
    cancel_visit,
    get_active_visit,
    get_clinic_name_for_visit,
    get_stages,
)
from .main_menu import show_main_menu


async def ask_cancel_visit(event: CallbackQuery, profile: Profile) -> None:
    lang = norm_lang(profile.language)
    if event.message:
        await event.message.answer(t(lang, "visit_cancel_confirm"), reply_markup=confirm_cancel(lang))


async def confirm_cancel_visit(event: CallbackQuery, profile: Profile) -> None:
    lang = norm_lang(profile.language)
    tg_id = event.from_user.id if event.from_user else None
    if tg_id is None:
        return
    active = get_active_visit(profile.id)
    if active:
        cancel_visit(active.id)
    clear_session(tg_id)
    if event.message:
        await event.message.answer(t(lang, "visit_cancelled"))
    await show_main_menu(event, profile)


async def finish_visit_from_menu(event: CallbackQuery, profile: Profile) -> None:
    lang = norm_lang(profile.language)
    active = get_active_visit(profile.id)
    if not active:
        await show_main_menu(event, profile)
        return
    stages = get_stages(active.id)
    have = {s.stage_type for s in stages}
    if not {"arrival", "specialist", "briefing", "completion"}.issubset(have):
        try:
            await event.answer(t(lang, "finish_blocked"), show_alert=True)
        except Exception:  # noqa: BLE001
            pass
        return
    tg_id = event.from_user.id if event.from_user else None
    if tg_id is not None:
        clear_session(tg_id)
    clinic = get_clinic_name_for_visit(active)
    if event.message:
        await event.message.answer(t(lang, "visit_completed", clinic=clinic))
    await show_main_menu(event, profile)
