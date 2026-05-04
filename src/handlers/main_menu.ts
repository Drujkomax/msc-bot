import type { Context } from "grammy";
import { t, normLang } from "../lib/i18n";
import { mainMenu } from "../lib/keyboards";
import { setSession } from "../lib/session";
import type { Profile } from "../lib/types";

export async function showMainMenu(ctx: Context, profile: Profile): Promise<void> {
  const lang = normLang(profile.language);
  const tgId = ctx.from?.id;
  if (!tgId) return;
  await setSession(tgId, "main_menu");
  const text = t(lang, "main_menu_title", { name: profile.full_name ?? profile.email ?? "" });
  if (ctx.callbackQuery?.message) {
    try {
      await ctx.editMessageText(text, { reply_markup: mainMenu(lang), parse_mode: "HTML" });
      return;
    } catch {
      /* fallback to send */
    }
  }
  await ctx.reply(text, { reply_markup: mainMenu(lang), parse_mode: "HTML" });
}
