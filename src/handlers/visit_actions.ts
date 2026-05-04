import type { Context } from "grammy";
import { t, normLang } from "../lib/i18n";
import { confirmCancel } from "../lib/keyboards";
import { getSession, clearSession, setSession } from "../lib/session";
import {
  cancelVisit,
  getStages,
  getActiveVisit,
  getClinicNameForVisit,
  getVisit,
} from "../lib/visits";
import type { Profile } from "../lib/types";
import { showMainMenu } from "./main_menu";

export async function askCancelVisit(ctx: Context, profile: Profile): Promise<void> {
  const lang = normLang(profile.language);
  await ctx.reply(t(lang, "visit_cancel_confirm"), { reply_markup: confirmCancel(lang) });
}

export async function confirmCancelVisit(ctx: Context, profile: Profile): Promise<void> {
  const lang = normLang(profile.language);
  const tgId = ctx.from!.id;
  const active = await getActiveVisit(profile.id);
  if (active) await cancelVisit(active.id);
  await clearSession(tgId);
  await ctx.reply(t(lang, "visit_cancelled"));
  await showMainMenu(ctx, profile);
}

export async function finishVisitFromMenu(ctx: Context, profile: Profile): Promise<void> {
  const lang = normLang(profile.language);
  const active = await getActiveVisit(profile.id);
  if (!active) {
    await showMainMenu(ctx, profile);
    return;
  }
  const stages = await getStages(active.id);
  const map = Object.fromEntries(stages.map((s) => [s.stage_type, s]));
  if (!map.arrival || !map.specialist || !map.briefing || !map.completion) {
    await ctx.answerCallbackQuery({ text: t(lang, "finish_blocked"), show_alert: true }).catch(() => {});
    return;
  }
  // если completion уже есть, ничего не нужно — просто закрываем
  const tgId = ctx.from!.id;
  await clearSession(tgId);
  const clinic = await getClinicNameForVisit(active);
  await ctx.reply(t(lang, "visit_completed", { clinic }));
  await showMainMenu(ctx, profile);
}
