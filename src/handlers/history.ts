import type { Context } from "grammy";
import { t, normLang } from "../lib/i18n";
import { backOnly } from "../lib/keyboards";
import { getRecentVisits, getClinicNameForVisit } from "../lib/visits";
import type { Profile } from "../lib/types";

const STATUS_EMOJI: Record<string, string> = {
  in_progress: "🟡",
  completed: "✅",
  abandoned: "⚪",
};

const OUTCOME_EMOJI: Record<string, string> = {
  success: "✅",
  interested: "🤔",
  rejected: "❌",
  postponed: "📅",
};

export async function showHistory(ctx: Context, profile: Profile): Promise<void> {
  const lang = normLang(profile.language);
  const visits = await getRecentVisits(profile.id, 10);
  if (visits.length === 0) {
    await ctx.reply(t(lang, "my_visits_empty"), { reply_markup: backOnly(lang) });
    return;
  }
  const lines = [t(lang, "my_visits_title"), ""];
  for (const v of visits) {
    const clinic = await getClinicNameForVisit(v);
    const date = new Date(v.started_at).toLocaleString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
    const outcome = v.outcome ? ` ${OUTCOME_EMOJI[v.outcome] ?? ""}` : "";
    lines.push(`${STATUS_EMOJI[v.status] ?? "•"} ${date} — ${clinic}${outcome}`);
  }
  await ctx.reply(lines.join("\n"), { reply_markup: backOnly(lang) });
}
