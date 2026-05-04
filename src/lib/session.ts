import { supabase } from "./supabase";
import type { BotSession } from "./types";

export async function getSession(telegramId: number): Promise<BotSession | null> {
  const { data, error } = await supabase
    .from("bot_sessions")
    .select("telegram_id, state, context")
    .eq("telegram_id", telegramId)
    .maybeSingle();
  if (error) return null;
  return (data as BotSession) ?? null;
}

export async function setSession(
  telegramId: number,
  state: string,
  context: Record<string, unknown> = {}
): Promise<void> {
  await supabase.from("bot_sessions").upsert(
    {
      telegram_id: telegramId,
      state,
      context,
      updated_at: new Date().toISOString(),
    },
    { onConflict: "telegram_id" }
  );
}

export async function clearSession(telegramId: number): Promise<void> {
  await supabase.from("bot_sessions").delete().eq("telegram_id", telegramId);
}

export async function patchContext(
  telegramId: number,
  patch: Record<string, unknown>
): Promise<void> {
  const session = await getSession(telegramId);
  const merged = { ...(session?.context ?? {}), ...patch };
  await setSession(telegramId, session?.state ?? "main_menu", merged);
}
