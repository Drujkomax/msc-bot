from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from .db import supabase
from .types import SpecialistData, Visit


def upsert_lead_from_specialist(
    rep_id: str,
    visit: Visit,
    data: SpecialistData,
    extra_notes: Optional[str] = None,
) -> None:
    """Mirror the specialist captured in a visit into `public.leads`.

    Idempotent per visit: a `[visit:<uuid>]` marker is embedded in `notes` so
    re-saving the specialist updates the same lead instead of duplicating it.
    """
    if not data.name:
        return

    # Resolve clinic name + city from the linked client (if any).
    company: Optional[str] = None
    city: Optional[str] = None
    if visit.client_id:
        res = (
            supabase.table("clients")
            .select("name, city")
            .eq("id", visit.client_id)
            .maybe_single()
            .execute()
        )
        c = res.data if res else None
        if c:
            company = c.get("name")
            city = c.get("city")
    elif visit.pending_clinic:
        company = visit.pending_clinic.get("name")

    marker = f"[visit:{visit.id}]"
    notes = "\n".join([p for p in (marker, (extra_notes or "").strip()) if p])

    payload = {
        "name": data.name,
        "position": data.position,
        "phone": data.phone,
        "email": data.email,
        "company": company,
        "city": city,
        "equipment_interest": data.equipment_interest,
        "budget_range": data.budget_range,
        "timeline": data.timeline,
        "lead_quality": data.lead_quality,
        "source": "manual",
        "stage": "new",
        "assigned_to": rep_id,
        "assigned_by": rep_id,
        "lead_created_date": datetime.now(timezone.utc).isoformat(),
        "notes": notes,
    }

    existing = (
        supabase.table("leads")
        .select("id")
        .ilike("notes", f"%{marker}%")
        .maybe_single()
        .execute()
    )
    existing_id = (existing.data or {}).get("id") if existing else None

    try:
        if existing_id:
            supabase.table("leads").update(payload).eq("id", existing_id).execute()
        else:
            supabase.table("leads").insert(payload).execute()
    except Exception as exc:  # noqa: BLE001
        print(f"upsert_lead_from_specialist failed: {exc}")
