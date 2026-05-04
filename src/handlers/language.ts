import type { Context } from "grammy";
import { supabase } from "../lib/supabase";
import { t, normLang } from "../lib/i18n";
import type { Profile } from "../lib/types";
import { showMainMenu } from "./main_menu";

export async function toggleLanguage(ctx: Context, profile: Profile): Promise<void> {
  const current = normLang(profile.language);
  const next = current === "ru" ? "uz" : "ru";
  await supabase.from("profiles").update({ language: next }).eq("id", profile.id);
  const updated: Profile = { ...profile, language: next };
  await ctx.answerCallbackQuery({ text: t(next, "lang_changed") }).catch(() => {});
  await showMainMenu(ctx, updated);
}
