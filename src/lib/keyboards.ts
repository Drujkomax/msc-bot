import { InlineKeyboard } from "grammy";
import type { Lang, StageType, VisitStage } from "./types";
import { t } from "./i18n";
import { stageMap } from "./visits";

export function mainMenu(lang: Lang): InlineKeyboard {
  return new InlineKeyboard()
    .text(t(lang, "btn_start_visit"), "visit:start")
    .row()
    .text(t(lang, "btn_my_visits"), "visit:history")
    .row()
    .text(t(lang, "btn_lang"), "lang:toggle");
}

export function clinicSearchResults(
  lang: Lang,
  results: Array<{ id: string; name: string; city?: string | null }>
): InlineKeyboard {
  const kb = new InlineKeyboard();
  for (const c of results) {
    const label = c.city ? `${c.name} • ${c.city}` : c.name;
    kb.text(label, `clinic:pick:${c.id}`).row();
  }
  kb.text(t(lang, "btn_new_clinic"), "clinic:new").row();
  kb.text(t(lang, "btn_cancel"), "visit:cancel_pick");
  return kb;
}

export function visitMenu(
  lang: Lang,
  stages: VisitStage[]
): InlineKeyboard {
  const map = stageMap(stages);
  const dot = (k: StageType) => (map[k] ? "✅" : "⏳");
  const allDone =
    map.arrival && map.specialist && map.briefing && map.completion;

  const kb = new InlineKeyboard()
    .text(`${dot("arrival")} ${t(lang, "stage_arrival")}`, "stage:arrival")
    .row()
    .text(`${dot("specialist")} ${t(lang, "stage_specialist")}`, "stage:specialist")
    .row()
    .text(`${dot("briefing")} ${t(lang, "stage_briefing")}`, "stage:briefing")
    .row()
    .text(`${dot("completion")} ${t(lang, "stage_completion")}`, "stage:completion")
    .row();

  if (allDone) {
    kb.text(t(lang, "btn_finish_visit"), "visit:finish").row();
  }
  kb.text(t(lang, "btn_cancel_visit"), "visit:cancel").row();
  kb.text(t(lang, "btn_open_main"), "menu:main");
  return kb;
}

export function doneOrSkip(lang: Lang, withSkip = false): InlineKeyboard {
  const kb = new InlineKeyboard().text(t(lang, "btn_done"), "stage:done");
  if (withSkip) kb.text(t(lang, "btn_skip"), "stage:skip");
  kb.row().text(t(lang, "btn_back"), "visit:menu");
  return kb;
}

export function backOnly(lang: Lang): InlineKeyboard {
  return new InlineKeyboard().text(t(lang, "btn_back"), "visit:menu");
}

export function cancelOnly(lang: Lang): InlineKeyboard {
  return new InlineKeyboard().text(t(lang, "btn_cancel"), "menu:main");
}

export function outcomePicker(lang: Lang): InlineKeyboard {
  return new InlineKeyboard()
    .text(t(lang, "outcome_success"), "outcome:success")
    .row()
    .text(t(lang, "outcome_interested"), "outcome:interested")
    .row()
    .text(t(lang, "outcome_rejected"), "outcome:rejected")
    .row()
    .text(t(lang, "outcome_postponed"), "outcome:postponed")
    .row()
    .text(t(lang, "btn_back"), "visit:menu");
}

export function confirmCancel(lang: Lang): InlineKeyboard {
  return new InlineKeyboard()
    .text(t(lang, "btn_yes_cancel"), "visit:cancel_confirm")
    .text(t(lang, "btn_back"), "visit:menu");
}

export function skipBack(lang: Lang): InlineKeyboard {
  return new InlineKeyboard()
    .text(t(lang, "btn_skip"), "stage:skip")
    .text(t(lang, "btn_back"), "visit:menu");
}
