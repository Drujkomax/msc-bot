from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


@dataclass(frozen=True)
class Settings:
    bot_token: str
    supabase_url: str
    supabase_service_role_key: str
    supabase_anon_key: str


settings = Settings(
    bot_token=_required("TELEGRAM_BOT_TOKEN"),
    supabase_url=_required("SUPABASE_URL"),
    supabase_service_role_key=_required("SUPABASE_SERVICE_ROLE_KEY"),
    supabase_anon_key=_required("SUPABASE_ANON_KEY"),
)
