import type { Context } from "grammy";
import { t, normLang } from "../lib/i18n";
import { backOnly, doneOrSkip, outcomePicker, skipBack } from "../lib/keyboards";
import { getSession, setSession, patchContext } from "../lib/session";
import {
  appendPhotosToStage,
  completeVisit,
  getActiveVisit,
  getStages,
  upsertStage,
} from "../lib/visits";
import { uploadTelegramPhoto } from "../lib/storage";
import type { Profile, StageType, VisitOutcome } from "../lib/types";
import { openVisitMenu } from "./visit_start";

const PHOTO_LIMIT = 10;

async function ensureActiveVisit(ctx: Context, profile: Profile): Promise<string | null> {
  const session = await getSession(ctx.from!.id);
  let visitId = session?.context?.visit_id as string | undefined;
  if (!visitId) {
    const active = await getActiveVisit(profile.id);
    visitId = active?.id;
  }
  if (!visitId) {
    const lang = normLang(profile.language);
    await ctx.reply(t(lang, "unknown_input"));
    return null;
  }
  return visitId;
}

// =============== Stage entry points ===============

export async function enterArrival(ctx: Context, profile: Profile): Promise<void> {
  // arrival фиксируется автоматически при старте; даём только дополнить заметку/фото
  const lang = normLang(profile.language);
  const tgId = ctx.from!.id;
  const visitId = await ensureActiveVisit(ctx, profile);
  if (!visitId) return;
  await setSession(tgId, "stage:arrival", { visit_id: visitId });
  await ctx.reply(t(lang, "stage_send_text_or_photo"), { reply_markup: doneOrSkip(lang, true) });
}

export async function enterSpecialist(ctx: Context, profile: Profile): Promise<void> {
  const lang = normLang(profile.language);
  const tgId = ctx.from!.id;
  const visitId = await ensureActiveVisit(ctx, profile);
  if (!visitId) return;
  await setSession(tgId, "stage:specialist:name", { visit_id: visitId, specialist: {} });
  await ctx.reply(t(lang, "specialist_name_prompt"), { reply_markup: backOnly(lang) });
}

export async function enterBriefing(ctx: Context, profile: Profile): Promise<void> {
  const lang = normLang(profile.language);
  const tgId = ctx.from!.id;
  const visitId = await ensureActiveVisit(ctx, profile);
  if (!visitId) return;
  await setSession(tgId, "stage:briefing", { visit_id: visitId });
  await ctx.reply(t(lang, "briefing_prompt"), { reply_markup: doneOrSkip(lang, false) });
}

export async function enterCompletion(ctx: Context, profile: Profile): Promise<void> {
  const lang = normLang(profile.language);
  const tgId = ctx.from!.id;
  const visitId = await ensureActiveVisit(ctx, profile);
  if (!visitId) return;
  await setSession(tgId, "stage:completion:outcome", { visit_id: visitId });
  await ctx.reply(t(lang, "completion_outcome_prompt"), { reply_markup: outcomePicker(lang) });
}

// =============== Text input dispatch ===============

export async function handleStageText(
  ctx: Context,
  profile: Profile,
  state: string,
  text: string
): Promise<boolean> {
  const lang = normLang(profile.language);
  const tgId = ctx.from!.id;
  const session = await getSession(tgId);
  const visitId = session?.context?.visit_id as string | undefined;
  if (!visitId) return false;

  switch (state) {
    case "stage:arrival":
    case "stage:briefing": {
      const stageType: StageType = state === "stage:arrival" ? "arrival" : "briefing";
      await upsertStage(visitId, stageType, { text_note: text });
      await ctx.reply(t(lang, "stage_saved"));
      return true;
    }
    case "stage:specialist:name": {
      const prev = (session?.context?.specialist ?? {}) as Record<string, unknown>;
      const sp = { ...prev, name: text };
      await setSession(tgId, "stage:specialist:position", { ...session?.context, specialist: sp });
      await ctx.reply(t(lang, "specialist_position_prompt"), { reply_markup: skipBack(lang) });
      return true;
    }
    case "stage:specialist:position": {
      const prev = (session?.context?.specialist ?? {}) as Record<string, unknown>;
      const sp = { ...prev, position: text };
      await setSession(tgId, "stage:specialist:phone", { ...session?.context, specialist: sp });
      await ctx.reply(t(lang, "specialist_phone_prompt"), { reply_markup: skipBack(lang) });
      return true;
    }
    case "stage:specialist:phone": {
      const prev = (session?.context?.specialist ?? {}) as Record<string, unknown>;
      const sp = { ...prev, phone: text };
      await upsertStage(visitId, "specialist", { payload: sp });
      await setSession(tgId, "stage:specialist:extras", { ...session?.context, specialist: sp });
      await ctx.reply(t(lang, "specialist_extras_prompt"), { reply_markup: doneOrSkip(lang, false) });
      return true;
    }
    case "stage:specialist:extras": {
      await upsertStage(visitId, "specialist", { text_note: text });
      await ctx.reply(t(lang, "stage_saved"));
      return true;
    }
    case "stage:completion:comment": {
      const outcome = session?.context?.outcome as VisitOutcome | undefined;
      if (!outcome) return false;
      await completeVisit(visitId, outcome, text);
      const stages = await getStages(visitId);
      // Завершение визита: показываем сообщение и чистим
      await ctx.reply(t(lang, "visit_completed", { clinic: "" }));
      await setSession(tgId, "main_menu");
      await openVisitMenu(ctx, profile, visitId);
      return true;
    }
  }
  return false;
}

// =============== Photo input ===============

export async function handleStagePhoto(
  ctx: Context,
  profile: Profile,
  state: string,
  fileId: string
): Promise<boolean> {
  const lang = normLang(profile.language);
  const tgId = ctx.from!.id;
  const session = await getSession(tgId);
  const visitId = session?.context?.visit_id as string | undefined;
  if (!visitId) return false;

  const stageMap: Record<string, StageType | undefined> = {
    "stage:arrival": "arrival",
    "stage:briefing": "briefing",
    "stage:specialist:extras": "specialist",
    "stage:completion:comment": "completion",
  };
  const stageType = stageMap[state];
  if (!stageType) return false;

  const stages = await getStages(visitId);
  const existing = stages.find((s) => s.stage_type === stageType);
  if ((existing?.photo_urls.length ?? 0) >= PHOTO_LIMIT) {
    await ctx.reply(t(lang, "photo_limit_reached"));
    return true;
  }

  try {
    const path = await uploadTelegramPhoto(fileId, visitId, stageType);
    const next = await appendPhotosToStage(visitId, stageType, [path]);
    await ctx.reply(t(lang, "photo_received", { count: next.photo_urls.length }));
  } catch (err) {
    console.error("Photo upload failed", err);
    await ctx.reply("⚠️ Не удалось сохранить фото, попробуйте ещё раз.");
  }
  return true;
}

// =============== Outcome selection ===============

export async function handleOutcomePick(
  ctx: Context,
  profile: Profile,
  outcome: VisitOutcome
): Promise<void> {
  const lang = normLang(profile.language);
  const tgId = ctx.from!.id;
  const session = await getSession(tgId);
  const visitId = session?.context?.visit_id as string | undefined;
  if (!visitId) return;
  await setSession(tgId, "stage:completion:comment", { visit_id: visitId, outcome });
  await ctx.reply(t(lang, "completion_comment_prompt"), { reply_markup: doneOrSkip(lang, true) });
}

// =============== Done / Skip from kb ===============

export async function handleStageDone(ctx: Context, profile: Profile): Promise<void> {
  const tgId = ctx.from!.id;
  const session = await getSession(tgId);
  const visitId = session?.context?.visit_id as string | undefined;

  if (session?.state === "stage:completion:comment") {
    const outcome = session?.context?.outcome as VisitOutcome | undefined;
    if (visitId && outcome) {
      await completeVisit(visitId, outcome, null);
    }
  }

  if (visitId) {
    await openVisitMenu(ctx, profile, visitId);
  }
}

export async function handleStageSkip(ctx: Context, profile: Profile): Promise<void> {
  const tgId = ctx.from!.id;
  const session = await getSession(tgId);
  const visitId = session?.context?.visit_id as string | undefined;
  const lang = normLang(profile.language);

  // Pre-set defaults for specialist stage
  if (session?.state === "stage:specialist:position") {
    const sp = (session?.context?.specialist ?? {}) as Record<string, unknown>;
    await setSession(tgId, "stage:specialist:phone", { ...session?.context, specialist: sp });
    await ctx.reply(t(lang, "specialist_phone_prompt"), { reply_markup: skipBack(lang) });
    return;
  }
  if (session?.state === "stage:specialist:phone") {
    const sp = (session?.context?.specialist ?? {}) as Record<string, unknown>;
    if (visitId) await upsertStage(visitId, "specialist", { payload: sp });
    await setSession(tgId, "stage:specialist:extras", { ...session?.context, specialist: sp });
    await ctx.reply(t(lang, "specialist_extras_prompt"), { reply_markup: doneOrSkip(lang, false) });
    return;
  }
  if (session?.state === "stage:completion:comment") {
    const outcome = session?.context?.outcome as VisitOutcome | undefined;
    if (visitId && outcome) await completeVisit(visitId, outcome, null);
    if (visitId) await openVisitMenu(ctx, profile, visitId);
    return;
  }

  if (visitId) await openVisitMenu(ctx, profile, visitId);
}
