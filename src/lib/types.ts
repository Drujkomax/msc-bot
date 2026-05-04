export type Lang = "ru" | "uz";

export type StageType = "arrival" | "specialist" | "briefing" | "completion";

export type VisitOutcome = "success" | "interested" | "rejected" | "postponed";

export interface Profile {
  id: string;
  email: string | null;
  full_name: string | null;
  telegram_id: number | null;
  language: Lang | "en" | null;
  role?: string | null;
}

export interface BotSession {
  telegram_id: number;
  state: string;
  context: Record<string, unknown>;
}

export interface Visit {
  id: string;
  rep_id: string;
  client_id: string | null;
  pending_clinic: { name: string; address?: string } | null;
  status: "in_progress" | "completed" | "abandoned";
  outcome: VisitOutcome | null;
  outcome_comment: string | null;
  started_at: string;
  completed_at: string | null;
}

export interface VisitStage {
  id: string;
  visit_id: string;
  stage_type: StageType;
  payload: Record<string, unknown>;
  text_note: string | null;
  photo_urls: string[];
  completed_at: string;
}

export interface ClientRow {
  id: string;
  name: string;
  city?: string | null;
  address?: string | null;
}
