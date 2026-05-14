from __future__ import annotations

from datetime import datetime

from aiogram.types import CallbackQuery

from ..i18n import norm_lang, t
from ..keyboards import back_only
from ..types import Profile
from ..visits import get_clinic_name_for_visit, get_recent_visits

STATUS_EMOJI = {"in_progress": "🟡", "completed": "✅", "abandoned": "⚪"}
OUTCOME_EMOJI = {"success": "✅", "interested": "🤔", "rejected": "❌", "postponed": "📅"}


async def show_history(event: CallbackQuery, profile: Profile) -> None:
    lang = norm_lang(profile.language)
    message = event.message
    if message is None:
        return
    visits = get_recent_visits(profile.id, 10)
    if not visits:
        await message.answer(t(lang, "my_visits_empty"), reply_markup=back_only(lang))
        return

    lines = [t(lang, "my_visits_title"), ""]
    for v in visits:
        clinic = get_clinic_name_for_visit(v)
        try:
            dt = datetime.fromisoformat(v.started_at.replace("Z", "+00:00"))
            date = dt.strftime("%d.%m %H:%M")
        except Exception:  # noqa: BLE001
            date = v.started_at
        outcome = f" {OUTCOME_EMOJI.get(v.outcome or '', '')}" if v.outcome else ""
        lines.append(f"{STATUS_EMOJI.get(v.status, '•')} {date} — {clinic}{outcome}")

    await message.answer("\n".join(lines), reply_markup=back_only(lang))
