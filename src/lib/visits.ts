import { supabase } from "./supabase";
import type { ClientRow, StageType, Visit, VisitOutcome, VisitStage } from "./types";

export async function getActiveVisit(repId: string): Promise<Visit | null> {
  const { data } = await supabase
    .from("visits")
    .select("*")
    .eq("rep_id", repId)
    .eq("status", "in_progress")
    .maybeSingle();
  return (data as Visit) ?? null;
}

export async function getVisit(visitId: string): Promise<Visit | null> {
  const { data } = await supabase.from("visits").select("*").eq("id", visitId).maybeSingle();
  return (data as Visit) ?? null;
}

export async function getStages(visitId: string): Promise<VisitStage[]> {
  const { data } = await supabase
    .from("visit_stages")
    .select("*")
    .eq("visit_id", visitId)
    .order("completed_at", { ascending: true });
  return (data as VisitStage[]) ?? [];
}

export async function searchClinics(query: string, limit = 5): Promise<ClientRow[]> {
  const { data } = await supabase
    .from("clients")
    .select("id, name, city, address")
    .ilike("name", `%${query}%`)
    .eq("archived", false)
    .order("name")
    .limit(limit);
  return (data as ClientRow[]) ?? [];
}

export async function startVisitWithExistingClinic(
  repId: string,
  clientId: string
): Promise<Visit> {
  const { data, error } = await supabase
    .from("visits")
    .insert({ rep_id: repId, client_id: clientId, status: "in_progress" })
    .select("*")
    .single();
  if (error) throw error;

  await upsertStage(data.id, "arrival", {});
  return data as Visit;
}

export async function startVisitWithNewClinic(
  repId: string,
  clinic: { name: string; address?: string }
): Promise<Visit> {
  const { data, error } = await supabase
    .from("visits")
    .insert({ rep_id: repId, pending_clinic: clinic, status: "in_progress" })
    .select("*")
    .single();
  if (error) throw error;

  await upsertStage(data.id, "arrival", {});
  return data as Visit;
}

export async function upsertStage(
  visitId: string,
  stageType: StageType,
  fields: {
    payload?: Record<string, unknown>;
    text_note?: string | null;
    photo_urls?: string[];
  }
): Promise<VisitStage> {
  const { data: existing } = await supabase
    .from("visit_stages")
    .select("*")
    .eq("visit_id", visitId)
    .eq("stage_type", stageType)
    .maybeSingle();

  if (existing) {
    const merged = {
      payload: { ...(existing.payload as Record<string, unknown>), ...(fields.payload ?? {}) },
      text_note: fields.text_note !== undefined ? fields.text_note : existing.text_note,
      photo_urls: fields.photo_urls ?? existing.photo_urls,
      completed_at: new Date().toISOString(),
    };
    const { data, error } = await supabase
      .from("visit_stages")
      .update(merged)
      .eq("id", existing.id)
      .select("*")
      .single();
    if (error) throw error;
    return data as VisitStage;
  }

  const { data, error } = await supabase
    .from("visit_stages")
    .insert({
      visit_id: visitId,
      stage_type: stageType,
      payload: fields.payload ?? {},
      text_note: fields.text_note ?? null,
      photo_urls: fields.photo_urls ?? [],
    })
    .select("*")
    .single();
  if (error) throw error;
  return data as VisitStage;
}

export async function appendPhotosToStage(
  visitId: string,
  stageType: StageType,
  newUrls: string[]
): Promise<VisitStage> {
  const stage = await upsertStage(visitId, stageType, {});
  const combined = [...(stage.photo_urls ?? []), ...newUrls].slice(0, 10);
  return upsertStage(visitId, stageType, { photo_urls: combined });
}

export async function completeVisit(
  visitId: string,
  outcome: VisitOutcome,
  comment: string | null
): Promise<void> {
  await supabase
    .from("visits")
    .update({
      outcome,
      outcome_comment: comment,
      status: "completed",
      completed_at: new Date().toISOString(),
    })
    .eq("id", visitId);
  await upsertStage(visitId, "completion", {
    payload: { outcome, comment },
    text_note: comment,
  });
}

export async function cancelVisit(visitId: string): Promise<void> {
  await supabase.from("visits").delete().eq("id", visitId);
}

export async function getRecentVisits(repId: string, limit = 10): Promise<Visit[]> {
  const { data } = await supabase
    .from("visits")
    .select("*")
    .eq("rep_id", repId)
    .order("started_at", { ascending: false })
    .limit(limit);
  return (data as Visit[]) ?? [];
}

export async function getClinicNameForVisit(visit: Visit): Promise<string> {
  if (visit.client_id) {
    const { data } = await supabase
      .from("clients")
      .select("name")
      .eq("id", visit.client_id)
      .maybeSingle();
    return (data?.name as string) ?? "—";
  }
  return visit.pending_clinic?.name ?? "—";
}

export function stageMap(stages: VisitStage[]): Record<StageType, VisitStage | undefined> {
  const map: Record<StageType, VisitStage | undefined> = {
    arrival: undefined,
    specialist: undefined,
    briefing: undefined,
    completion: undefined,
  };
  for (const s of stages) map[s.stage_type] = s;
  return map;
}
