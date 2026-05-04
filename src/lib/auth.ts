import { supabase, supabaseAnon } from "./supabase";
import type { Profile } from "./types";

export async function getProfileByTelegramId(telegramId: number): Promise<Profile | null> {
  const { data, error } = await supabase
    .from("profiles")
    .select("id, email, full_name, telegram_id, language")
    .eq("telegram_id", telegramId)
    .maybeSingle();
  if (error) {
    console.error("getProfileByTelegramId", error);
    return null;
  }
  if (!data) return null;
  const role = await getRole(data.id);
  return { ...data, role };
}

async function getRole(userId: string): Promise<string | null> {
  const { data } = await supabase
    .from("user_roles")
    .select("role")
    .eq("user_id", userId)
    .maybeSingle();
  return (data?.role as string) ?? null;
}

/**
 * Verifies email + password against Supabase Auth. On success, links the
 * Telegram account to the matching profile and returns it.
 */
export async function loginAndLink(
  email: string,
  password: string,
  telegramId: number,
  telegramUsername: string | undefined
): Promise<Profile | null> {
  const { data, error } = await supabaseAnon.auth.signInWithPassword({
    email: email.trim().toLowerCase(),
    password,
  });
  if (error || !data.user) {
    console.warn("loginAndLink failed:", error?.message);
    return null;
  }
  const userId = data.user.id;

  // Ensure another telegram_id is not already bound to this profile (or this telegram_id to another profile)
  const { data: existingByTg } = await supabase
    .from("profiles")
    .select("id")
    .eq("telegram_id", telegramId)
    .maybeSingle();
  if (existingByTg && existingByTg.id !== userId) {
    // Force re-bind: clear the old binding
    await supabase
      .from("profiles")
      .update({ telegram_id: null, telegram_username: null })
      .eq("id", existingByTg.id);
  }

  const { data: updated, error: updErr } = await supabase
    .from("profiles")
    .update({
      telegram_id: telegramId,
      telegram_username: telegramUsername ?? null,
      telegram_link_code: null,
      telegram_link_code_expires_at: null,
    })
    .eq("id", userId)
    .select("id, email, full_name, telegram_id, language")
    .single();

  if (updErr || !updated) {
    console.error("loginAndLink update failed:", updErr);
    return null;
  }

  const role = await getRole(updated.id);
  return { ...updated, role };
}

export function canStartVisit(role: string | null | undefined): boolean {
  return ["salesperson", "sales_manager", "director", "admin"].includes(role ?? "");
}
