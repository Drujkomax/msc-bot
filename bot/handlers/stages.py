from __future__ import annotations

from typing import Optional

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from ..i18n import norm_lang, t
from ..keyboards import (
    back_only,
    briefing_category_picker,
    budget_picker,
    done_or_skip,
    equipment_picker,
    outcome_picker,
    quality_picker,
    skip_back,
    timeline_picker,
)
from ..leads import upsert_lead_from_specialist
from ..session import get_session, set_session
from ..storage import upload_telegram_photo
from ..types import Profile, SpecialistData
from ..visits import (
    append_photos_to_stage,
    complete_visit,
    get_active_visit,
    get_stages,
    get_visit,
    upsert_stage,
)
from .visit_start import open_visit_menu

PHOTO_LIMIT = 10
BRIEFING_QUESTION_COUNT = 10

# States where Done/Skip should appear (vs Done only) after a save acknowledgement.
_FREE_INPUT_WITH_SKIP = {"stage:arrival", "stage:completion:comment"}
_FREE_INPUT_NO_SKIP = {"stage:briefing:notes", "stage:specialist:extras"}
_PICKER_STATES = {
    "stage:briefing:category",
    "stage:specialist:equipment",
    "stage:specialist:budget",
    "stage:specialist:timeline",
    "stage:specialist:quality",
    "stage:completion:outcome",
}


def _briefing_q_state(n: int) -> str:
    return f"stage:briefing:q:{n}"


def _is_briefing_q_state(state: Optional[str]) -> bool:
    return bool(state) and state.startswith("stage:briefing:q:")  # type: ignore[union-attr]


def _briefing_q_n(state: str) -> int:
    return int(state.rsplit(":", 1)[1])


def _briefing_question(lang: str, category: str, n: int) -> str:
    return t(lang, f"briefing_q_{category}_{n}")


def _briefing_prompt(lang: str, category: str, n: int) -> str:
    cat = t(lang, f"cat_{category}")
    return f"{t(lang, 'briefing_progress', n=n, category=cat)}\n\n{_briefing_question(lang, category, n)}"


def _briefing_payload(category: str, answers: list[dict]) -> dict:
    return {"category": category, "answers": answers}


def _ensure_visit_id(profile: Profile, tg_id: int) -> Optional[str]:
    session = get_session(tg_id)
    vid = (session.context if session else {}).get("visit_id")
    if vid:
        return vid
    active = get_active_visit(profile.id)
    return active.id if active else None


def _specialist_from_session(ctx: dict) -> SpecialistData:
    return SpecialistData.from_dict(ctx.get("specialist") or {})


async def _persist_specialist_and_save(visit_id: str, rep_id: str, sp: SpecialistData) -> None:
    upsert_stage(visit_id, "specialist", payload=sp.to_dict())
    visit = get_visit(visit_id)
    if visit:
        upsert_lead_from_specialist(rep_id, visit, sp)


async def _edit_or_send(
    event: CallbackQuery,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
) -> None:
    """Edit the message the callback was attached to (standard inline UX).
    Falls back to a fresh message if Telegram refuses the edit (old / deleted)."""
    if event.message is None:
        return
    try:
        await event.message.edit_text(text, reply_markup=reply_markup)
        return
    except TelegramBadRequest:
        await event.message.answer(text, reply_markup=reply_markup)


# =============== Stage entry points ===============

async def enter_arrival(event: CallbackQuery, profile: Profile) -> None:
    lang = norm_lang(profile.language)
    tg_id = event.from_user.id if event.from_user else None
    if tg_id is None:
        return
    visit_id = _ensure_visit_id(profile, tg_id)
    if not visit_id:
        if event.message:
            await event.message.answer(t(lang, "unknown_input"))
        return
    set_session(tg_id, "stage:arrival", {"visit_id": visit_id})
    await _edit_or_send(event, t(lang, "stage_send_text_or_photo"), done_or_skip(lang, True))


async def enter_specialist(event: CallbackQuery, profile: Profile) -> None:
    lang = norm_lang(profile.language)
    tg_id = event.from_user.id if event.from_user else None
    if tg_id is None:
        return
    visit_id = _ensure_visit_id(profile, tg_id)
    if not visit_id:
        if event.message:
            await event.message.answer(t(lang, "unknown_input"))
        return
    set_session(tg_id, "stage:specialist:name", {"visit_id": visit_id, "specialist": {}})
    await _edit_or_send(event, t(lang, "specialist_name_prompt"), back_only(lang))


async def enter_briefing(event: CallbackQuery, profile: Profile) -> None:
    lang = norm_lang(profile.language)
    tg_id = event.from_user.id if event.from_user else None
    if tg_id is None:
        return
    visit_id = _ensure_visit_id(profile, tg_id)
    if not visit_id:
        if event.message:
            await event.message.answer(t(lang, "unknown_input"))
        return
    set_session(tg_id, "stage:briefing:category", {"visit_id": visit_id})
    await _edit_or_send(event, t(lang, "briefing_category_prompt"), briefing_category_picker(lang))


async def enter_completion(event: CallbackQuery, profile: Profile) -> None:
    lang = norm_lang(profile.language)
    tg_id = event.from_user.id if event.from_user else None
    if tg_id is None:
        return
    visit_id = _ensure_visit_id(profile, tg_id)
    if not visit_id:
        if event.message:
            await event.message.answer(t(lang, "unknown_input"))
        return
    set_session(tg_id, "stage:completion:outcome", {"visit_id": visit_id})
    await _edit_or_send(event, t(lang, "completion_outcome_prompt"), outcome_picker(lang))


# =============== Text input dispatch ===============

async def handle_stage_text(
    message: Message,
    profile: Profile,
    state: str,
    text: str,
) -> bool:
    lang = norm_lang(profile.language)
    tg_id = message.from_user.id if message.from_user else None
    if tg_id is None:
        return False
    session = get_session(tg_id)
    ctx = (session.context if session else {}) or {}
    visit_id: Optional[str] = ctx.get("visit_id")
    if not visit_id:
        return False

    # User typed text where only buttons are expected → polite hint, keep state.
    if state in _PICKER_STATES:
        await message.answer(t(lang, "use_buttons_hint"))
        return True

    # Briefing questionnaire: each text answer advances to the next question.
    if _is_briefing_q_state(state):
        await _advance_briefing(message, profile, text)
        return True

    if state == "stage:arrival":
        upsert_stage(visit_id, "arrival", text_note=text)
        await message.answer(t(lang, "stage_saved_more"), reply_markup=done_or_skip(lang, True))
        return True

    if state == "stage:briefing:notes":
        upsert_stage(visit_id, "briefing", text_note=text)
        await message.answer(t(lang, "stage_saved_more"), reply_markup=done_or_skip(lang, False))
        return True

    if state == "stage:specialist:name":
        sp = _specialist_from_session(ctx)
        sp.name = text
        set_session(tg_id, "stage:specialist:position", {**ctx, "specialist": sp.to_dict()})
        await message.answer(t(lang, "specialist_position_prompt"), reply_markup=skip_back(lang))
        return True

    if state == "stage:specialist:position":
        sp = _specialist_from_session(ctx)
        sp.position = text
        set_session(tg_id, "stage:specialist:phone", {**ctx, "specialist": sp.to_dict()})
        await message.answer(t(lang, "specialist_phone_prompt"), reply_markup=skip_back(lang))
        return True

    if state == "stage:specialist:phone":
        sp = _specialist_from_session(ctx)
        sp.phone = text
        set_session(tg_id, "stage:specialist:email", {**ctx, "specialist": sp.to_dict()})
        await message.answer(t(lang, "specialist_email_prompt"), reply_markup=skip_back(lang))
        return True

    if state == "stage:specialist:email":
        sp = _specialist_from_session(ctx)
        sp.email = text
        set_session(tg_id, "stage:specialist:equipment", {**ctx, "specialist": sp.to_dict()})
        await message.answer(t(lang, "specialist_equipment_prompt"), reply_markup=equipment_picker(lang))
        return True

    if state == "stage:specialist:extras":
        sp = _specialist_from_session(ctx)
        upsert_stage(visit_id, "specialist", text_note=text)
        visit = get_visit(visit_id)
        if visit and sp.name:
            upsert_lead_from_specialist(profile.id, visit, sp, text)
        await message.answer(t(lang, "stage_saved_more"), reply_markup=done_or_skip(lang, False))
        return True

    if state == "stage:completion:comment":
        outcome = ctx.get("outcome")
        if not outcome:
            return False
        complete_visit(visit_id, outcome, text)
        await message.answer(t(lang, "visit_completed", clinic=""))
        set_session(tg_id, "main_menu")
        # No edit context here (text-driven); re-render menu by faking a Message-based call.
        from .main_menu import show_main_menu
        await show_main_menu(message, profile)
        return True

    return False


# =============== Picker callbacks ===============

async def handle_briefing_category_pick(
    event: CallbackQuery,
    profile: Profile,
    category: str,
) -> None:
    lang = norm_lang(profile.language)
    tg_id = event.from_user.id if event.from_user else None
    if tg_id is None:
        return
    session = get_session(tg_id)
    ctx = (session.context if session else {}) or {}
    visit_id: Optional[str] = ctx.get("visit_id")
    if not visit_id:
        return
    answers: list[dict] = []
    upsert_stage(visit_id, "briefing", payload=_briefing_payload(category, answers))
    set_session(
        tg_id,
        _briefing_q_state(1),
        {**ctx, "briefing_category": category, "briefing_answers": answers},
    )
    await _edit_or_send(event, _briefing_prompt(lang, category, 1), skip_back(lang))


async def _advance_briefing(
    event_or_message,
    profile: Profile,
    answer: Optional[str],
) -> None:
    """Append the (optional) answer to the current briefing question, then move to
    the next question or to the notes step if all 10 are answered.

    Accepts either a CallbackQuery (Skip click) or a Message (text answer)."""
    lang = norm_lang(profile.language)
    is_callback = isinstance(event_or_message, CallbackQuery)
    user = event_or_message.from_user
    if user is None:
        return
    tg_id = user.id
    session = get_session(tg_id)
    ctx = (session.context if session else {}) or {}
    state = session.state if session else ""
    visit_id: Optional[str] = ctx.get("visit_id")
    category: Optional[str] = ctx.get("briefing_category")
    if not (visit_id and category and _is_briefing_q_state(state)):
        return

    n = _briefing_q_n(state)
    question_text = _briefing_question(lang, category, n)
    answers = list(ctx.get("briefing_answers") or [])
    answers.append({"q": question_text, "a": answer})
    upsert_stage(visit_id, "briefing", payload=_briefing_payload(category, answers))

    if n < BRIEFING_QUESTION_COUNT:
        new_state = _briefing_q_state(n + 1)
        new_ctx = {**ctx, "briefing_answers": answers}
        set_session(tg_id, new_state, new_ctx)
        next_prompt = _briefing_prompt(lang, category, n + 1)
        if is_callback:
            await _edit_or_send(event_or_message, next_prompt, skip_back(lang))
        else:
            await event_or_message.answer(next_prompt, reply_markup=skip_back(lang))
        return

    # All 10 answered → notes step
    new_ctx = {**ctx, "briefing_answers": answers}
    set_session(tg_id, "stage:briefing:notes", new_ctx)
    notes_prompt = t(lang, "briefing_notes_prompt")
    if is_callback:
        await _edit_or_send(event_or_message, notes_prompt, done_or_skip(lang, False))
    else:
        await event_or_message.answer(notes_prompt, reply_markup=done_or_skip(lang, False))


async def handle_specialist_pick(
    event: CallbackQuery,
    profile: Profile,
    prefix: str,
    value: str,
) -> None:
    lang = norm_lang(profile.language)
    tg_id = event.from_user.id if event.from_user else None
    if tg_id is None:
        return
    session = get_session(tg_id)
    ctx = (session.context if session else {}) or {}
    visit_id: Optional[str] = ctx.get("visit_id")
    if not visit_id:
        return
    sp = _specialist_from_session(ctx)

    if prefix == "eq":
        sp.equipment_interest = value
        set_session(tg_id, "stage:specialist:budget", {**ctx, "specialist": sp.to_dict()})
        await _edit_or_send(event, t(lang, "specialist_budget_prompt"), budget_picker(lang))
        return
    if prefix == "bg":
        sp.budget_range = value
        set_session(tg_id, "stage:specialist:timeline", {**ctx, "specialist": sp.to_dict()})
        await _edit_or_send(event, t(lang, "specialist_timeline_prompt"), timeline_picker(lang))
        return
    if prefix == "tl":
        sp.timeline = value
        set_session(tg_id, "stage:specialist:quality", {**ctx, "specialist": sp.to_dict()})
        await _edit_or_send(event, t(lang, "specialist_quality_prompt"), quality_picker(lang))
        return
    if prefix == "lq":
        sp.lead_quality = value
        await _persist_specialist_and_save(visit_id, profile.id, sp)
        set_session(tg_id, "stage:specialist:extras", {**ctx, "specialist": sp.to_dict()})
        combined = f"{t(lang, 'lead_saved')}\n\n{t(lang, 'specialist_extras_prompt')}"
        await _edit_or_send(event, combined, done_or_skip(lang, False))
        return


# =============== Photo input ===============

async def handle_stage_photo(message: Message, profile: Profile, state: str, file_id: str) -> bool:
    lang = norm_lang(profile.language)
    tg_id = message.from_user.id if message.from_user else None
    if tg_id is None:
        return False
    session = get_session(tg_id)
    ctx = (session.context if session else {}) or {}
    visit_id: Optional[str] = ctx.get("visit_id")
    if not visit_id:
        return False

    # Photo while in a picker-only step → polite hint.
    if state in _PICKER_STATES:
        await message.answer(t(lang, "use_buttons_hint"))
        return True

    # Briefing is text-only: redirect photo uploads to the arrival stage.
    if state == "stage:briefing:notes" or _is_briefing_q_state(state):
        await message.answer(t(lang, "photo_briefing_redirect"))
        return True

    stage_map = {
        "stage:arrival": "arrival",
        "stage:specialist:extras": "specialist",
        "stage:completion:comment": "completion",
    }
    stage_type = stage_map.get(state)
    if not stage_type:
        return False

    stages = get_stages(visit_id)
    existing = next((s for s in stages if s.stage_type == stage_type), None)
    if existing and len(existing.photo_urls) >= PHOTO_LIMIT:
        await message.answer(t(lang, "photo_limit_reached"))
        return True

    try:
        path = await upload_telegram_photo(file_id, visit_id, stage_type)
        nxt = append_photos_to_stage(visit_id, stage_type, [path])
        with_skip = state in _FREE_INPUT_WITH_SKIP
        await message.answer(
            t(lang, "photo_received_more", count=len(nxt.photo_urls)),
            reply_markup=done_or_skip(lang, with_skip),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Photo upload failed: {exc}")
        await message.answer(f"⚠️ Не удалось сохранить фото: {exc}")
    return True


# =============== Outcome selection ===============

async def handle_outcome_pick(event: CallbackQuery, profile: Profile, outcome: str) -> None:
    lang = norm_lang(profile.language)
    tg_id = event.from_user.id if event.from_user else None
    if tg_id is None:
        return
    session = get_session(tg_id)
    ctx = (session.context if session else {}) or {}
    visit_id = ctx.get("visit_id")
    if not visit_id:
        return
    set_session(tg_id, "stage:completion:comment", {"visit_id": visit_id, "outcome": outcome})
    await _edit_or_send(event, t(lang, "completion_comment_prompt"), done_or_skip(lang, True))


# =============== Done / Skip from kb ===============

async def handle_stage_done(event: CallbackQuery, profile: Profile) -> None:
    tg_id = event.from_user.id if event.from_user else None
    if tg_id is None:
        return
    session = get_session(tg_id)
    ctx = (session.context if session else {}) or {}
    visit_id = ctx.get("visit_id")

    if session and session.state == "stage:completion:comment":
        outcome = ctx.get("outcome")
        if visit_id and outcome:
            complete_visit(visit_id, outcome, None)

    if visit_id:
        await open_visit_menu(event, profile, visit_id)


async def handle_stage_skip(event: CallbackQuery, profile: Profile) -> None:
    lang = norm_lang(profile.language)
    tg_id = event.from_user.id if event.from_user else None
    if tg_id is None:
        return
    session = get_session(tg_id)
    ctx = (session.context if session else {}) or {}
    visit_id = ctx.get("visit_id")
    state = session.state if session else None

    if _is_briefing_q_state(state):
        await _advance_briefing(event, profile, None)
        return

    if state == "stage:specialist:position":
        set_session(tg_id, "stage:specialist:phone", ctx)
        await _edit_or_send(event, t(lang, "specialist_phone_prompt"), skip_back(lang))
        return
    if state == "stage:specialist:phone":
        set_session(tg_id, "stage:specialist:email", ctx)
        await _edit_or_send(event, t(lang, "specialist_email_prompt"), skip_back(lang))
        return
    if state == "stage:specialist:email":
        set_session(tg_id, "stage:specialist:equipment", ctx)
        await _edit_or_send(event, t(lang, "specialist_equipment_prompt"), equipment_picker(lang))
        return
    if state == "stage:specialist:equipment":
        set_session(tg_id, "stage:specialist:budget", ctx)
        await _edit_or_send(event, t(lang, "specialist_budget_prompt"), budget_picker(lang))
        return
    if state == "stage:specialist:budget":
        set_session(tg_id, "stage:specialist:timeline", ctx)
        await _edit_or_send(event, t(lang, "specialist_timeline_prompt"), timeline_picker(lang))
        return
    if state == "stage:specialist:timeline":
        set_session(tg_id, "stage:specialist:quality", ctx)
        await _edit_or_send(event, t(lang, "specialist_quality_prompt"), quality_picker(lang))
        return
    if state == "stage:specialist:quality":
        sp = _specialist_from_session(ctx)
        if visit_id:
            await _persist_specialist_and_save(visit_id, profile.id, sp)
        set_session(tg_id, "stage:specialist:extras", {**ctx, "specialist": sp.to_dict()})
        combined = f"{t(lang, 'lead_saved')}\n\n{t(lang, 'specialist_extras_prompt')}"
        await _edit_or_send(event, combined, done_or_skip(lang, False))
        return
    if state == "stage:completion:comment":
        outcome = ctx.get("outcome")
        if visit_id and outcome:
            complete_visit(visit_id, outcome, None)
        if visit_id:
            await open_visit_menu(event, profile, visit_id)
        return

    if visit_id:
        await open_visit_menu(event, profile, visit_id)
