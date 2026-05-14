from __future__ import annotations

from typing import Iterable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .i18n import t
from .types import VisitStage
from .visits import stage_map


def _kb(rows: list[list[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _btn(label: str, callback_data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=label, callback_data=callback_data)


def main_menu(lang: str) -> InlineKeyboardMarkup:
    return _kb(
        [
            [_btn(t(lang, "btn_start_visit"), "visit:start")],
            [_btn(t(lang, "btn_my_visits"), "visit:history")],
            [_btn(t(lang, "btn_lang"), "lang:toggle")],
        ]
    )


def clinic_search_results(lang: str, results: Iterable[dict]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for c in results:
        label = f"{c['name']} • {c['city']}" if c.get("city") else c["name"]
        rows.append([_btn(label, f"clinic:pick:{c['id']}")])
    rows.append([_btn(t(lang, "btn_new_clinic"), "clinic:new")])
    rows.append([_btn(t(lang, "btn_cancel"), "visit:cancel_pick")])
    return _kb(rows)


def visit_menu(lang: str, stages: list[VisitStage]) -> InlineKeyboardMarkup:
    m = stage_map(stages)
    dot = lambda k: "✅" if m.get(k) else "⏳"  # noqa: E731
    all_done = all(m.get(k) for k in ("arrival", "specialist", "briefing", "completion"))

    rows: list[list[InlineKeyboardButton]] = [
        [_btn(f"{dot('arrival')} {t(lang, 'stage_arrival')}", "stage:arrival")],
        [_btn(f"{dot('specialist')} {t(lang, 'stage_specialist')}", "stage:specialist")],
        [_btn(f"{dot('briefing')} {t(lang, 'stage_briefing')}", "stage:briefing")],
        [_btn(f"{dot('completion')} {t(lang, 'stage_completion')}", "stage:completion")],
    ]
    if all_done:
        rows.append([_btn(t(lang, "btn_finish_visit"), "visit:finish")])
    rows.append([_btn(t(lang, "btn_cancel_visit"), "visit:cancel")])
    rows.append([_btn(t(lang, "btn_open_main"), "menu:main")])
    return _kb(rows)


def done_or_skip(lang: str, with_skip: bool = False) -> InlineKeyboardMarkup:
    first_row = [_btn(t(lang, "btn_done"), "stage:done")]
    if with_skip:
        first_row.append(_btn(t(lang, "btn_skip"), "stage:skip"))
    return _kb([first_row, [_btn(t(lang, "btn_back"), "visit:menu")]])


def back_only(lang: str) -> InlineKeyboardMarkup:
    return _kb([[_btn(t(lang, "btn_back"), "visit:menu")]])


def cancel_only(lang: str) -> InlineKeyboardMarkup:
    return _kb([[_btn(t(lang, "btn_cancel"), "menu:main")]])


def outcome_picker(lang: str) -> InlineKeyboardMarkup:
    return _kb(
        [
            [_btn(t(lang, "outcome_success"), "outcome:success")],
            [_btn(t(lang, "outcome_interested"), "outcome:interested")],
            [_btn(t(lang, "outcome_rejected"), "outcome:rejected")],
            [_btn(t(lang, "outcome_postponed"), "outcome:postponed")],
            [_btn(t(lang, "btn_back"), "visit:menu")],
        ]
    )


def confirm_cancel(lang: str) -> InlineKeyboardMarkup:
    return _kb(
        [[_btn(t(lang, "btn_yes_cancel"), "visit:cancel_confirm"), _btn(t(lang, "btn_back"), "visit:menu")]]
    )


def skip_back(lang: str) -> InlineKeyboardMarkup:
    return _kb([[_btn(t(lang, "btn_skip"), "stage:skip"), _btn(t(lang, "btn_back"), "visit:menu")]])


def _picker(
    lang: str,
    rows: list[list[tuple[str, str]]],
) -> InlineKeyboardMarkup:
    kb_rows = [[_btn(label, cb) for (label, cb) in row] for row in rows]
    kb_rows.append([_btn(t(lang, "btn_skip"), "stage:skip"), _btn(t(lang, "btn_back"), "visit:menu")])
    return _kb(kb_rows)


def equipment_picker(lang: str) -> InlineKeyboardMarkup:
    return _picker(
        lang,
        [
            [(t(lang, "eq_mrt_mskt"), "eq:mrt_mskt"), (t(lang, "eq_ultrasound"), "eq:ultrasound")],
            [(t(lang, "eq_xray"), "eq:xray"), (t(lang, "eq_gynecology"), "eq:gynecology")],
            [(t(lang, "eq_laboratory"), "eq:laboratory"), (t(lang, "eq_surgical"), "eq:surgical")],
            [(t(lang, "eq_physiotherapy"), "eq:physiotherapy"), (t(lang, "eq_resuscitation"), "eq:resuscitation")],
            [(t(lang, "eq_other"), "eq:other")],
        ],
    )


def budget_picker(lang: str) -> InlineKeyboardMarkup:
    return _picker(
        lang,
        [
            [(t(lang, "bg_3k_5k"), "bg:3k_5k"), (t(lang, "bg_5k_10k"), "bg:5k_10k")],
            [(t(lang, "bg_10k_50k"), "bg:10k_50k"), (t(lang, "bg_50k_100k"), "bg:50k_100k")],
            [(t(lang, "bg_100k_500k"), "bg:100k_500k"), (t(lang, "bg_over_500k"), "bg:over_500k")],
            [(t(lang, "bg_not_specified"), "bg:not_specified")],
        ],
    )


def timeline_picker(lang: str) -> InlineKeyboardMarkup:
    return _picker(
        lang,
        [
            [(t(lang, "tl_immediate"), "tl:immediate"), (t(lang, "tl_1_month"), "tl:1_month")],
            [(t(lang, "tl_3_months"), "tl:3_months"), (t(lang, "tl_6_months"), "tl:6_months")],
            [(t(lang, "tl_1_year"), "tl:1_year"), (t(lang, "tl_not_specified"), "tl:not_specified")],
        ],
    )


def briefing_category_picker(lang: str) -> InlineKeyboardMarkup:
    return _kb(
        [
            [_btn(t(lang, "bc_diagnostic"), "bc:diagnostic")],
            [_btn(t(lang, "bc_laboratory"), "bc:laboratory")],
            [_btn(t(lang, "bc_dental"), "bc:dental")],
            [_btn(t(lang, "btn_back"), "visit:menu")],
        ]
    )


def quality_picker(lang: str) -> InlineKeyboardMarkup:
    return _picker(
        lang,
        [
            [(t(lang, "lq_A"), "lq:A")],
            [(t(lang, "lq_B"), "lq:B")],
            [(t(lang, "lq_C"), "lq:C")],
        ],
    )
