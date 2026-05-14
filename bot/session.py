from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from .db import supabase
from .types import BotSession


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_session(telegram_id: int) -> Optional[BotSession]:
    try:
        res = (
            supabase.table("bot_sessions")
            .select("telegram_id, state, context")
            .eq("telegram_id", telegram_id)
            .maybe_single()
            .execute()
        )
    except Exception as exc:  # noqa: BLE001
        print(f"get_session error: {exc}")
        return None
    data = res.data if res else None
    if not data:
        return None
    return BotSession(
        telegram_id=data["telegram_id"],
        state=data.get("state") or "main_menu",
        context=data.get("context") or {},
    )


def set_session(telegram_id: int, state: str, context: Optional[dict[str, Any]] = None) -> None:
    payload = {
        "telegram_id": telegram_id,
        "state": state,
        "context": context or {},
        "updated_at": _now_iso(),
    }
    supabase.table("bot_sessions").upsert(payload, on_conflict="telegram_id").execute()


def clear_session(telegram_id: int) -> None:
    supabase.table("bot_sessions").delete().eq("telegram_id", telegram_id).execute()


def patch_context(telegram_id: int, patch: dict[str, Any]) -> None:
    session = get_session(telegram_id)
    merged = {**(session.context if session else {}), **patch}
    set_session(telegram_id, session.state if session else "main_menu", merged)
