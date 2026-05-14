from __future__ import annotations

from dataclasses import asdict
from typing import Union

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from ..i18n import norm_lang, t
from ..keyboards import clinic_search_results, visit_menu
from ..session import clear_session, get_session, set_session
from ..types import Profile
from ..visits import (
    get_active_visit,
    get_clinic_name_for_visit,
    get_stages,
    get_visit,
    search_clinics,
    start_visit_with_existing_clinic,
    start_visit_with_new_clinic,
)


async def start_new_visit_flow(event: CallbackQuery, profile: Profile) -> None:
    lang = norm_lang(profile.language)
    tg_id = event.from_user.id if event.from_user else None
    if tg_id is None or event.message is None:
        return

    active = get_active_visit(profile.id)
    if active:
        try:
            await event.answer(t(lang, "visit_already_active"))
        except Exception:  # noqa: BLE001
            pass
        await open_visit_menu(event, profile, active.id)
        return

    set_session(tg_id, "picking_clinic")
    await event.message.answer(t(lang, "pick_clinic_prompt"))


async def handle_clinic_search(message: Message, profile: Profile, query: str) -> None:
    lang = norm_lang(profile.language)
    if len(query.strip()) < 2:
        await message.answer(t(lang, "pick_clinic_too_short"))
        return
    results = [
        {"id": c.id, "name": c.name, "city": c.city}
        for c in search_clinics(query)
    ]
    if not results:
        await message.answer(
            t(lang, "pick_clinic_no_match"),
            reply_markup=clinic_search_results(lang, []),
        )
        return
    await message.answer(f"🔎 «{query}»", reply_markup=clinic_search_results(lang, results))


async def pick_existing_clinic(event: CallbackQuery, profile: Profile, client_id: str) -> None:
    lang = norm_lang(profile.language)
    tg_id = event.from_user.id if event.from_user else None
    if tg_id is None or event.message is None:
        return
    visit = start_visit_with_existing_clinic(profile.id, client_id)
    clear_session(tg_id)
    await open_visit_menu(event, profile, visit.id)
    clinic = get_clinic_name_for_visit(visit)
    await event.message.answer(t(lang, "visit_started", clinic=clinic))


async def prompt_new_clinic_name(event: CallbackQuery, profile: Profile) -> None:
    lang = norm_lang(profile.language)
    tg_id = event.from_user.id if event.from_user else None
    if tg_id is None or event.message is None:
        return
    set_session(tg_id, "new_clinic_name")
    await event.message.answer(t(lang, "new_clinic_name_prompt"))


async def capture_new_clinic_name(message: Message, profile: Profile, name: str) -> None:
    lang = norm_lang(profile.language)
    tg_id = message.from_user.id if message.from_user else None
    if tg_id is None:
        return
    set_session(tg_id, "new_clinic_address", {"name": name})
    await message.answer(t(lang, "new_clinic_address_prompt"))


async def capture_new_clinic_address_or_skip(
    message: Message,
    profile: Profile,
    address: str | None,
) -> None:
    lang = norm_lang(profile.language)
    tg_id = message.from_user.id if message.from_user else None
    if tg_id is None:
        return
    session = get_session(tg_id)
    name = (session.context if session else {}).get("name") or ""
    if not name:
        return
    clinic: dict = {"name": name}
    if address:
        clinic["address"] = address
    visit = start_visit_with_new_clinic(profile.id, clinic)
    clear_session(tg_id)
    await open_visit_menu(message, profile, visit.id)
    await message.answer(t(lang, "visit_started", clinic=name))


async def open_visit_menu(
    event: Union[Message, CallbackQuery],
    profile: Profile,
    visit_id: str,
) -> None:
    lang = norm_lang(profile.language)
    tg_id = event.from_user.id if event.from_user else None
    if tg_id is None:
        return

    visit = get_visit(visit_id)
    if not visit:
        return
    stages = get_stages(visit_id)
    clinic = get_clinic_name_for_visit(visit)
    set_session(tg_id, "visit_menu", {"visit_id": visit_id})

    text = t(lang, "visit_menu_title", clinic=clinic)
    kb = visit_menu(lang, stages)

    if isinstance(event, CallbackQuery) and event.message:
        try:
            await event.message.edit_text(text, reply_markup=kb)
            return
        except TelegramBadRequest:
            pass
        await event.message.answer(text, reply_markup=kb)
        return

    if isinstance(event, Message):
        await event.answer(text, reply_markup=kb)
