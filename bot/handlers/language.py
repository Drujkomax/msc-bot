from __future__ import annotations

from dataclasses import replace

from aiogram.types import CallbackQuery

from ..db import supabase
from ..i18n import norm_lang, t
from ..types import Profile
from .main_menu import show_main_menu


async def toggle_language(event: CallbackQuery, profile: Profile) -> None:
    current = norm_lang(profile.language)
    nxt = "uz" if current == "ru" else "ru"
    supabase.table("profiles").update({"language": nxt}).eq("id", profile.id).execute()
    updated = replace(profile, language=nxt)
    try:
        await event.answer(t(nxt, "lang_changed"))
    except Exception:  # noqa: BLE001
        pass
    await show_main_menu(event, updated)
