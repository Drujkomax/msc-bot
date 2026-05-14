from __future__ import annotations

from supabase import Client, create_client

from .config import settings

# Service-role client: bypasses RLS, used for all bot DB operations.
supabase: Client = create_client(settings.supabase_url, settings.supabase_service_role_key)

# Anon client: only for verifying employee credentials via sign_in_with_password.
supabase_anon: Client = create_client(settings.supabase_url, settings.supabase_anon_key)
