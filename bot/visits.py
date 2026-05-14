from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from .db import supabase
from .types import ClientRow, Visit, VisitStage


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_visit(row: dict) -> Visit:
    return Visit(
        id=row["id"],
        rep_id=row["rep_id"],
        client_id=row.get("client_id"),
        pending_clinic=row.get("pending_clinic"),
        status=row.get("status") or "in_progress",
        outcome=row.get("outcome"),
        outcome_comment=row.get("outcome_comment"),
        started_at=row.get("started_at") or _now_iso(),
        completed_at=row.get("completed_at"),
    )


def _to_stage(row: dict) -> VisitStage:
    return VisitStage(
        id=row["id"],
        visit_id=row["visit_id"],
        stage_type=row["stage_type"],
        payload=row.get("payload") or {},
        text_note=row.get("text_note"),
        photo_urls=row.get("photo_urls") or [],
        completed_at=row.get("completed_at") or _now_iso(),
    )


def get_active_visit(rep_id: str) -> Optional[Visit]:
    res = (
        supabase.table("visits")
        .select("*")
        .eq("rep_id", rep_id)
        .eq("status", "in_progress")
        .maybe_single()
        .execute()
    )
    data = res.data if res else None
    return _to_visit(data) if data else None


def get_visit(visit_id: str) -> Optional[Visit]:
    res = supabase.table("visits").select("*").eq("id", visit_id).maybe_single().execute()
    data = res.data if res else None
    return _to_visit(data) if data else None


def get_stages(visit_id: str) -> list[VisitStage]:
    res = (
        supabase.table("visit_stages")
        .select("*")
        .eq("visit_id", visit_id)
        .order("completed_at", desc=False)
        .execute()
    )
    rows = res.data or []
    return [_to_stage(r) for r in rows]


def stage_map(stages: list[VisitStage]) -> dict[str, Optional[VisitStage]]:
    out: dict[str, Optional[VisitStage]] = {
        "arrival": None,
        "specialist": None,
        "briefing": None,
        "completion": None,
    }
    for s in stages:
        out[s.stage_type] = s
    return out


def search_clinics(query: str, limit: int = 5) -> list[ClientRow]:
    res = (
        supabase.table("clients")
        .select("id, name, city, address")
        .ilike("name", f"%{query}%")
        .eq("archived", False)
        .order("name")
        .limit(limit)
        .execute()
    )
    rows = res.data or []
    return [ClientRow(id=r["id"], name=r["name"], city=r.get("city"), address=r.get("address")) for r in rows]


def start_visit_with_existing_clinic(rep_id: str, client_id: str) -> Visit:
    res = (
        supabase.table("visits")
        .insert({"rep_id": rep_id, "client_id": client_id, "status": "in_progress"})
        .execute()
    )
    row = (res.data or [None])[0]
    if not row:
        raise RuntimeError("visit insert returned no row")
    visit = _to_visit(row)
    upsert_stage(visit.id, "arrival", payload={})
    return visit


def start_visit_with_new_clinic(rep_id: str, clinic: dict[str, Any]) -> Visit:
    res = (
        supabase.table("visits")
        .insert({"rep_id": rep_id, "pending_clinic": clinic, "status": "in_progress"})
        .execute()
    )
    row = (res.data or [None])[0]
    if not row:
        raise RuntimeError("visit insert returned no row")
    visit = _to_visit(row)
    upsert_stage(visit.id, "arrival", payload={})
    return visit


def upsert_stage(
    visit_id: str,
    stage_type: str,
    *,
    payload: Optional[dict[str, Any]] = None,
    text_note: Optional[str] = ...,  # type: ignore[assignment]
    photo_urls: Optional[list[str]] = None,
) -> VisitStage:
    """`text_note=...` (Ellipsis sentinel) means "don't touch"; pass None to clear."""
    existing_res = (
        supabase.table("visit_stages")
        .select("*")
        .eq("visit_id", visit_id)
        .eq("stage_type", stage_type)
        .maybe_single()
        .execute()
    )
    existing = existing_res.data if existing_res else None

    if existing:
        merged_payload = {**(existing.get("payload") or {}), **(payload or {})}
        merged: dict[str, Any] = {
            "payload": merged_payload,
            "photo_urls": photo_urls if photo_urls is not None else existing.get("photo_urls") or [],
            "completed_at": _now_iso(),
        }
        if text_note is not ...:
            merged["text_note"] = text_note
        res = (
            supabase.table("visit_stages")
            .update(merged)
            .eq("id", existing["id"])
            .execute()
        )
        row = (res.data or [None])[0] or {**existing, **merged}
        return _to_stage(row)

    insert_payload = {
        "visit_id": visit_id,
        "stage_type": stage_type,
        "payload": payload or {},
        "text_note": None if text_note is ... else text_note,
        "photo_urls": photo_urls or [],
    }
    res = supabase.table("visit_stages").insert(insert_payload).execute()
    row = (res.data or [None])[0]
    if not row:
        raise RuntimeError("visit_stages insert returned no row")
    return _to_stage(row)


def append_photos_to_stage(visit_id: str, stage_type: str, new_urls: list[str]) -> VisitStage:
    stage = upsert_stage(visit_id, stage_type)
    combined = (stage.photo_urls + new_urls)[:10]
    return upsert_stage(visit_id, stage_type, photo_urls=combined)


def complete_visit(visit_id: str, outcome: str, comment: Optional[str]) -> None:
    supabase.table("visits").update(
        {
            "outcome": outcome,
            "outcome_comment": comment,
            "status": "completed",
            "completed_at": _now_iso(),
        }
    ).eq("id", visit_id).execute()
    upsert_stage(
        visit_id,
        "completion",
        payload={"outcome": outcome, "comment": comment},
        text_note=comment,
    )


def cancel_visit(visit_id: str) -> None:
    supabase.table("visits").delete().eq("id", visit_id).execute()


def get_recent_visits(rep_id: str, limit: int = 10) -> list[Visit]:
    res = (
        supabase.table("visits")
        .select("*")
        .eq("rep_id", rep_id)
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
    )
    rows = res.data or []
    return [_to_visit(r) for r in rows]


def get_clinic_name_for_visit(visit: Visit) -> str:
    if visit.client_id:
        res = (
            supabase.table("clients")
            .select("name")
            .eq("id", visit.client_id)
            .maybe_single()
            .execute()
        )
        name = (res.data or {}).get("name") if res else None
        return name or "—"
    if visit.pending_clinic:
        return visit.pending_clinic.get("name") or "—"
    return "—"
