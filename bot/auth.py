from __future__ import annotations

from typing import Optional

from .db import supabase, supabase_anon
from .types import Profile

_ALLOWED_ROLES = {"salesperson", "sales_manager", "director", "admin"}


def _get_role(user_id: str) -> Optional[str]:
    try:
        res = (
            supabase.table("user_roles")
            .select("role")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
    except Exception as exc:  # noqa: BLE001
        print(f"get_role error: {exc}")
        return None
    return (res.data or {}).get("role") if res else None


def _row_to_profile(data: dict, role: Optional[str]) -> Profile:
    return Profile(
        id=data["id"],
        email=data.get("email"),
        full_name=data.get("full_name"),
        telegram_id=data.get("telegram_id"),
        language=data.get("language"),
        role=role,
    )


def get_profile_by_telegram_id(telegram_id: int) -> Optional[Profile]:
    try:
        res = (
            supabase.table("profiles")
            .select("id, email, full_name, telegram_id, language")
            .eq("telegram_id", telegram_id)
            .maybe_single()
            .execute()
        )
    except Exception as exc:  # noqa: BLE001
        print(f"get_profile_by_telegram_id error: {exc}")
        return None
    if not res or not res.data:
        return None
    role = _get_role(res.data["id"])
    return _row_to_profile(res.data, role)


def login_and_link(
    email: str,
    password: str,
    telegram_id: int,
    telegram_username: Optional[str],
) -> Optional[Profile]:
    """Verify credentials, link telegram_id to the profile, return the profile."""
    try:
        auth = supabase_anon.auth.sign_in_with_password(
            {"email": email.strip().lower(), "password": password}
        )
    except Exception as exc:  # noqa: BLE001
        print(f"login_and_link sign_in failed: {exc}")
        return None
    user = getattr(auth, "user", None)
    if not user:
        return None
    user_id = user.id

    # Force-rebind if another profile already holds this telegram_id.
    try:
        existing = (
            supabase.table("profiles")
            .select("id")
            .eq("telegram_id", telegram_id)
            .maybe_single()
            .execute()
        )
    except Exception:  # noqa: BLE001
        existing = None
    if existing and existing.data and existing.data["id"] != user_id:
        supabase.table("profiles").update(
            {"telegram_id": None, "telegram_username": None}
        ).eq("id", existing.data["id"]).execute()

    updated = (
        supabase.table("profiles")
        .update(
            {
                "telegram_id": telegram_id,
                "telegram_username": telegram_username,
                "telegram_link_code": None,
                "telegram_link_code_expires_at": None,
            }
        )
        .eq("id", user_id)
        .execute()
    )
    rows = updated.data or []
    if not rows:
        return None
    role = _get_role(user_id)
    row = rows[0]
    # the update returns full row only when select() was chained; re-fetch to be safe
    if "email" not in row:
        fetched = (
            supabase.table("profiles")
            .select("id, email, full_name, telegram_id, language")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
        row = (fetched.data if fetched else None) or row
    return _row_to_profile(row, role)


def can_start_visit(role: Optional[str]) -> bool:
    return (role or "") in _ALLOWED_ROLES
