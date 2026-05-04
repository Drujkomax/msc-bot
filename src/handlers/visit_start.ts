import type { Context } from "grammy";
import { t, normLang } from "../lib/i18n";
import {
  clinicSearchResults,
  visitMenu,
} from "../lib/keyboards";
import { clearSession, setSession, patchContext, getSession } from "../lib/session";
import {
  getActiveVisit,
  searchClinics,
  startVisitWithExistingClinic,
  startVisitWithNewClinic,
  getStages,
  getClinicNameForVisit,
  getVisit,
} from "../lib/visits";
import type { Profile } from "../lib/types";

export async function startNewVisitFlow(ctx: Context, profile: Profile): Promise<void> {
  const lang = normLang(profile.language);
  const tgId = ctx.from?.id;
  if (!tgId) return;

  const active = await getActiveVisit(profile.id);
  if (active) {
    await ctx.answerCallbackQuery({ text: t(lang, "visit_already_active") }).catch(() => {});
    await openVisitMenu(ctx, profile, active.id);
    return;
  }

  await setSession(tgId, "picking_clinic");
  await ctx.reply(t(lang, "pick_clinic_prompt"));
}

export async function handleClinicSearch(ctx: Context, profile: Profile, query: string): Promise<void> {
  const lang = normLang(profile.language);
  if (query.trim().length < 2) {
    await ctx.reply(t(lang, "pick_clinic_too_short"));
    return;
  }
  const results = await searchClinics(query);
  if (results.length === 0) {
    await ctx.reply(t(lang, "pick_clinic_no_match"), {
      reply_markup: clinicSearchResults(lang, []),
    });
    return;
  }
  await ctx.reply(`🔎 «${query}»`, {
    reply_markup: clinicSearchResults(lang, results),
  });
}

export async function pickExistingClinic(ctx: Context, profile: Profile, clientId: string): Promise<void> {
  const lang = normLang(profile.language);
  const tgId = ctx.from?.id;
  if (!tgId) return;
  const visit = await startVisitWithExistingClinic(profile.id, clientId);
  await clearSession(tgId);
  await openVisitMenu(ctx, profile, visit.id);
  const clinic = await getClinicNameForVisit(visit);
  await ctx.reply(t(lang, "visit_started", { clinic }), { parse_mode: "HTML" });
}

export async function promptNewClinicName(ctx: Context, profile: Profile): Promise<void> {
  const lang = normLang(profile.language);
  const tgId = ctx.from?.id;
  if (!tgId) return;
  await setSession(tgId, "new_clinic_name");
  await ctx.reply(t(lang, "new_clinic_name_prompt"));
}

export async function captureNewClinicName(ctx: Context, profile: Profile, name: string): Promise<void> {
  const lang = normLang(profile.language);
  const tgId = ctx.from?.id;
  if (!tgId) return;
  await setSession(tgId, "new_clinic_address", { name });
  await ctx.reply(t(lang, "new_clinic_address_prompt"));
}

export async function captureNewClinicAddressOrSkip(
  ctx: Context,
  profile: Profile,
  address: string | null
): Promise<void> {
  const lang = normLang(profile.language);
  const tgId = ctx.from?.id;
  if (!tgId) return;
  const session = await getSession(tgId);
  const name = (session?.context?.name as string) ?? "";
  if (!name) return;
  const visit = await startVisitWithNewClinic(profile.id, { name, ...(address ? { address } : {}) });
  await clearSession(tgId);
  await openVisitMenu(ctx, profile, visit.id);
  await ctx.reply(t(lang, "visit_started", { clinic: name }), { parse_mode: "HTML" });
}

export async function openVisitMenu(ctx: Context, profile: Profile, visitId: string): Promise<void> {
  const lang = normLang(profile.language);
  const tgId = ctx.from?.id;
  if (!tgId) return;

  const visit = await getVisit(visitId);
  if (!visit) return;

  const stages = await getStages(visitId);
  const clinic = await getClinicNameForVisit(visit);
  await setSession(tgId, "visit_menu", { visit_id: visitId });

  const text = t(lang, "visit_menu_title", { clinic });
  const kb = visitMenu(lang, stages);

  if (ctx.callbackQuery?.message) {
    try {
      await ctx.editMessageText(text, { reply_markup: kb, parse_mode: "HTML" });
      return;
    } catch {
      /* fall through */
    }
  }
  await ctx.reply(text, { reply_markup: kb, parse_mode: "HTML" });
}
