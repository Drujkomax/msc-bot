import { createClient } from "@supabase/supabase-js";
import { env } from "./env";

/** Service-role client: bypasses RLS, used for all read/write operations from the bot. */
export const supabase = createClient(
  env.SUPABASE_URL,
  env.SUPABASE_SERVICE_ROLE_KEY,
  {
    auth: { persistSession: false, autoRefreshToken: false },
  }
);

/** Anon client: used only to verify employee credentials via signInWithPassword. */
export const supabaseAnon = createClient(
  env.SUPABASE_URL,
  env.SUPABASE_ANON_KEY,
  {
    auth: { persistSession: false, autoRefreshToken: false },
  }
);
