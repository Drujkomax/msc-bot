import type { Context } from "grammy";
import { getProfileByTelegramId, loginAndLink, canStartVisit } from "../lib/auth";
import { t, normLang } from "../lib/i18n";
import { mainMenu } from "../lib/keyboards";
import { clearSession, setSession, getSession } from "../lib/session";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export async function handleStart(ctx: Context): Promise<void> {
  const tgId = ctx.from?.id;
  if (!tgId) return;

  const existing = await getProfileByTelegramId(tgId);
  if (existing) {
    if (!canStartVisit(existing.role)) {
      const lang = normLang(existing.language);
      await ctx.reply(t(lang, "login_role_denied"));
      return;
    }
    const lang = normLang(existing.language);
    await clearSession(tgId);
    await setSession(tgId, "main_menu");
    await ctx.reply(
      t(lang, "main_menu_title", { name: existing.full_name ?? existing.email ?? "" }),
      { reply_markup: mainMenu(lang), parse_mode: "HTML" }
    );
    return;
  }

  await setSession(tgId, "awaiting_email");
  await ctx.reply(t("ru", "unlinked_prompt"), { parse_mode: "HTML" });
}

/** Returns true if the message was consumed by the auth flow. */
export async function handleAuthFlow(ctx: Context, text: string): Promise<boolean> {
  const tgId = ctx.from?.id;
  if (!tgId) return false;
  const session = await getSession(tgId);
  if (!session) return false;

  if (session.state === "awaiting_email") {
    if (!EMAIL_RE.test(text)) {
      await ctx.reply(t("ru", "unlinked_prompt"), { parse_mode: "HTML" });
      return true;
    }
    await setSession(tgId, "awaiting_password", { email: text.trim().toLowerCase() });
    await ctx.reply(t("ru", "login_password_prompt"), { parse_mode: "HTML" });
    return true;
  }

  if (session.state === "awaiting_password") {
    const email = (session.context?.email as string) ?? "";
    // Try to delete the password message for hygiene (best-effort)
    if (ctx.message?.message_id) {
      ctx.api.deleteMessage(ctx.chat!.id, ctx.message.message_id).catch(() => {});
    }
    const linked = await loginAndLink(email, text, tgId, ctx.from?.username);
    if (!linked) {
      await setSession(tgId, "awaiting_email");
      await ctx.reply(t("ru", "login_invalid"));
      return true;
    }
    if (!canStartVisit(linked.role)) {
      await clearSession(tgId);
      const lang = normLang(linked.language);
      await ctx.reply(t(lang, "login_role_denied"));
      return true;
    }
    const lang = normLang(linked.language);
    await setSession(tgId, "main_menu");
    await ctx.reply(t(lang, "linked_success", { name: linked.full_name ?? linked.email ?? "" }));
    await ctx.reply(t(lang, "main_menu_title", { name: linked.full_name ?? linked.email ?? "" }), {
      reply_markup: mainMenu(lang),
      parse_mode: "HTML",
    });
    return true;
  }

  return false;
}
