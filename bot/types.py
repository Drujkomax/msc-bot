from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional

Lang = Literal["ru", "uz"]
StageType = Literal["arrival", "specialist", "briefing", "completion"]
VisitOutcome = Literal["success", "interested", "rejected", "postponed"]

EquipmentInterest = Literal[
    "mrt_mskt",
    "ultrasound",
    "xray",
    "gynecology",
    "laboratory",
    "surgical",
    "physiotherapy",
    "resuscitation",
    "other",
]
BudgetRange = Literal[
    "3k_5k", "5k_10k", "10k_50k", "50k_100k", "100k_500k", "over_500k", "not_specified"
]
Timeline = Literal["immediate", "1_month", "3_months", "6_months", "1_year", "not_specified"]
LeadQuality = Literal["A", "B", "C"]


@dataclass
class Profile:
    id: str
    email: Optional[str]
    full_name: Optional[str]
    telegram_id: Optional[int]
    language: Optional[str]
    role: Optional[str] = None


@dataclass
class BotSession:
    telegram_id: int
    state: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class Visit:
    id: str
    rep_id: str
    client_id: Optional[str]
    pending_clinic: Optional[dict[str, Any]]
    status: str
    outcome: Optional[str]
    outcome_comment: Optional[str]
    started_at: str
    completed_at: Optional[str]


@dataclass
class VisitStage:
    id: str
    visit_id: str
    stage_type: str
    payload: dict[str, Any]
    text_note: Optional[str]
    photo_urls: list[str]
    completed_at: str


@dataclass
class ClientRow:
    id: str
    name: str
    city: Optional[str] = None
    address: Optional[str] = None


@dataclass
class SpecialistData:
    name: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    equipment_interest: Optional[str] = None
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    lead_quality: Optional[str] = None

    @classmethod
    def from_dict(cls, raw: Optional[dict[str, Any]]) -> "SpecialistData":
        if not raw:
            return cls()
        return cls(
            name=raw.get("name"),
            position=raw.get("position"),
            phone=raw.get("phone"),
            email=raw.get("email"),
            equipment_interest=raw.get("equipment_interest"),
            budget_range=raw.get("budget_range"),
            timeline=raw.get("timeline"),
            lead_quality=raw.get("lead_quality"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}
