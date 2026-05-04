import { Bot, GrammyError, HttpError } from "grammy";
import { env } from "./lib/env";
import { getProfileByTelegramId, canStartVisit } from "./lib/auth";
import { getSession } from "./lib/session";
import { handleStart, handleAuthFlow } from "./handlers/start";
import { showMainMenu } from "./handlers/main_menu";
import { showHistory } from "./handlers/history";
import {
  startNewVisitFlow,
  handleClinicSearch,
  pickExistingClinic,
  promptNewClinicName,
  captureNewClinicName,
  captureNewClinicAddressOrSkip,
  openVisitMenu,
} from "./handlers/visit_start";
import {
  enterArrival,
  enterBriefing,
  enterCompletion,
  enterSpecialist,
  handleOutcomePick,
  handleStageDone,
  handleStagePhoto,
  handleStageSkip,
  handleStageText,
} from "./handlers/stages";
import {
  askCancelVisit,
  confirmCancelVisit,
  finishVisitFromMenu,
} from "./handlers/visit_actions";
import { toggleLanguage } from "./handlers/language";
import type { VisitOutcome } from "./lib/types";
import { t, normLang } from "./lib/i18n";

const bot = new Bot(env.BOT_TOKEN);

bot.command("start", async (ctx) => {
  await handleStart(ctx);
});

bot.command("menu", async (ctx) => {
  const tgId = ctx.from?.id;
  if (!tgId) return;
  const profile = await getProfileByTelegramId(tgId);
  if (!profile) {
    await handleStart(ctx);
    return;
  }
  await showMainMenu(ctx, profile);
});

// =========== Callback queries ===========
bot.on("callback_query:data", async (ctx) => {
  const data = ctx.callbackQuery.data;
  const tgId = ctx.from?.id;
  if (!tgId || !data) return;
  await ctx.answerCallbackQuery().catch(() => {});

  const profile = await getProfileByTelegramId(tgId);
  if (!profile) {
    await handleStart(ctx);
    return;
  }

  const lang = normLang(profile.language);
  if (!canStartVisit(profile.role)) {
    await ctx.reply(t(lang, "unlinked_role_denied"));
    return;
  }

  // Routing
  if (data === "menu:main") return showMainMenu(ctx, profile);
  if (data === "lang:toggle") return toggleLanguage(ctx, profile);

  if (data === "visit:start") return startNewVisitFlow(ctx, profile);
  if (data === "visit:history") return showHistory(ctx, profile);
  if (data === "visit:menu") {
    const session = await getSession(tgId);
    const visitId = session?.context?.visit_id as string | undefined;
    if (visitId) return openVisitMenu(ctx, profile, visitId);
    return showMainMenu(ctx, profile);
  }
  if (data === "visit:cancel") return askCancelVisit(ctx, profile);
  if (data === "visit:cancel_confirm") return confirmCancelVisit(ctx, profile);
  if (data === "visit:cancel_pick") return showMainMenu(ctx, profile);
  if (data === "visit:finish") return finishVisitFromMenu(ctx, profile);

  if (data.startsWith("clinic:pick:")) {
    const clientId = data.slice("clinic:pick:".length);
    return pickExistingClinic(ctx, profile, clientId);
  }
  if (data === "clinic:new") return promptNewClinicName(ctx, profile);

  if (data === "stage:arrival") return enterArrival(ctx, profile);
  if (data === "stage:specialist") return enterSpecialist(ctx, profile);
  if (data === "stage:briefing") return enterBriefing(ctx, profile);
  if (data === "stage:completion") return enterCompletion(ctx, profile);
  if (data === "stage:done") return handleStageDone(ctx, profile);
  if (data === "stage:skip") return handleStageSkip(ctx, profile);

  if (data.startsWith("outcome:")) {
    const outcome = data.slice("outcome:".length) as VisitOutcome;
    return handleOutcomePick(ctx, profile, outcome);
  }
});

// =========== Photo messages ===========
bot.on("message:photo", async (ctx) => {
  const tgId = ctx.from?.id;
  if (!tgId) return;
  const profile = await getProfileByTelegramId(tgId);
  if (!profile) return;
  const session = await getSession(tgId);
  if (!session) return;
  const photos = ctx.message.photo;
  if (!photos || photos.length === 0) return;
  const largest = photos[photos.length - 1];
  if (!largest) return;
  await handleStagePhoto(ctx, profile, session.state, largest.file_id);
});

// =========== Text messages ===========
bot.on("message:text", async (ctx) => {
  const tgId = ctx.from?.id;
  if (!tgId) return;
  const text = ctx.message.text.trim();

  const profile = await getProfileByTelegramId(tgId);
  if (!profile) {
    const handled = await handleAuthFlow(ctx, text);
    if (!handled) {
      await handleStart(ctx);
    }
    return;
  }

  const lang = normLang(profile.language);
  if (!canStartVisit(profile.role)) {
    await ctx.reply(t(lang, "unlinked_role_denied"));
    return;
  }

  const session = await getSession(tgId);
  const state = session?.state ?? "main_menu";

  // global states (not in stages)
  if (state === "picking_clinic") {
    await handleClinicSearch(ctx, profile, text);
    return;
  }
  if (state === "new_clinic_name") {
    await captureNewClinicName(ctx, profile, text);
    return;
  }
  if (state === "new_clinic_address") {
    await captureNewClinicAddressOrSkip(ctx, profile, text);
    return;
  }

  if (state.startsWith("stage:")) {
    const handled = await handleStageText(ctx, profile, state, text);
    if (handled) return;
  }

  await ctx.reply(t(lang, "unknown_input"));
  await showMainMenu(ctx, profile);
});

// =========== Errors ===========
bot.catch((err) => {
  const ctx = err.ctx;
  console.error(`Error while handling update ${ctx.update.update_id}:`);
  if (err.error instanceof GrammyError) console.error("Grammy error:", err.error.description);
  else if (err.error instanceof HttpError) console.error("HTTP error:", err.error);
  else console.error("Unknown error:", err.error);
});

// =========== Boot ===========
console.log("MSC Visits Bot starting…");
bot.start({
  drop_pending_updates: true,
  onStart: (info) => console.log(`Bot @${info.username} is up.`),
});
