"""In-memory reference store.

Every entity follows the customer's data convention:
id(UUID) / org_id / site_id / created_at / created_by / updated_at / deleted_at(soft delete),
plus run_id so an end-to-end run can be purged in one shot.

Amounts are integer cents. No float anywhere.
"""
from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

ORG_ID = "org-demo"
SITE_ID = "site-hongqiao"
SALESPOOL = ["sp-alice", "sp-bob"]  # 线索按轮询规则分配
ROOMS = ["room-1201", "room-1202", "room-0805"]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


@dataclass
class Entity:
    id: str
    run_id: str
    org_id: str = ORG_ID
    site_id: str = SITE_ID
    created_at: str = field(default_factory=now)
    created_by: str = "system"
    updated_at: str = field(default_factory=now)
    deleted_at: str | None = None

    def touch(self, actor: str = "system") -> None:
        self.updated_at = now()
        self.created_by = self.created_by or actor


@dataclass
class Application(Entity):
    company: str = ""
    contact_name: str = ""
    contact_phone: str = ""
    intent: str = ""
    status: str = "submitted"


@dataclass
class Lead(Entity):
    application_id: str = ""
    company: str = ""
    assigned_to: str | None = None
    status: str = "new"  # new/assigned/contacted/visit_scheduled/visited/minutes_confirmed/quoted/contract_signed/rented/handover_claimed
    first_contact_at: str | None = None


@dataclass
class Visit(Entity):
    lead_id: str = ""
    code: str = ""
    scheduled_at: str = ""
    checked_in_at: str | None = None
    status: str = "scheduled"  # scheduled/checked_in


@dataclass
class Minutes(Entity):
    lead_id: str = ""
    summary: str = ""
    confirmed: bool = False


@dataclass
class Quote(Entity):
    lead_id: str = ""
    monthly_cents: int = 0
    discount_bps: int = 10000  # 10000 = 不打折；9500 = 9.5 折
    status: str = "draft"  # draft/approved


@dataclass
class Contract(Entity):
    quote_id: str = ""
    lead_id: str = ""
    room_id: str = ""
    signed_by_applicant: bool = False
    signed_by_org: bool = False
    status: str = "pending"  # pending/signed


@dataclass
class Room(Entity):
    room_no: str = ""
    status: str = "vacant"  # vacant/reserved/rented
    contract_id: str | None = None
    lead_id: str | None = None
    lease_run_id: str | None = None  # which smoke run is currently leasing this room


@dataclass
class Handover(Entity):
    room_id: str = ""
    lead_id: str = ""
    manager_id: str = ""
    status: str = "claimed"


@dataclass
class Member(Entity):
    lead_id: str = ""
    phone: str = ""
    verified: bool = False
    first_month_recommendations: list[dict[str, Any]] = field(default_factory=list)


class Store:
    """One process, one lock. Enough for a reference stub; production is PostgreSQL."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.tables: dict[str, dict[str, Entity]] = {
            "applications": {},
            "leads": {},
            "visits": {},
            "minutes": {},
            "quotes": {},
            "contracts": {},
            "rooms": {},
            "handovers": {},
            "members": {},
        }
        self._seq = 0
        self._seed_rooms()

    def _seed_rooms(self) -> None:
        for rid in ROOMS:
            room = Room(id=rid, run_id="seed", room_no=rid.split("-")[1], created_by="seed")
            self.tables["rooms"][rid] = room

    # -- helpers ---------------------------------------------------------
    def add(self, table: str, entity: Entity) -> Entity:
        with self._lock:
            self.tables[table][entity.id] = entity
            return entity

    def get(self, table: str, entity_id: str) -> Entity | None:
        with self._lock:
            obj = self.tables[table].get(entity_id)
            if obj is None or obj.deleted_at is not None:
                return None
            return obj

    def next_seq(self) -> int:
        with self._lock:
            self._seq += 1
            return self._seq

    def by_run(self, run_id: str) -> dict[str, list[Entity]]:
        with self._lock:
            out: dict[str, list[Entity]] = {}
            for name, rows in self.tables.items():
                hits = [o for o in rows.values() if o.run_id == run_id]
                if hits:
                    out[name] = hits
            return out

    def count_run(self, run_id: str) -> dict[str, int]:
        with self._lock:
            return {
                name: sum(1 for o in rows.values() if o.run_id == run_id)
                for name, rows in self.tables.items()
            }

    def purge_run(self, run_id: str) -> dict[str, int]:
        """Hard delete by run_id (the smoke run's own data only)."""
        with self._lock:
            removed: dict[str, int] = {}
            # rooms are seeded inventory: release instead of delete
            released = []
            for room in self.tables["rooms"].values():
                if room.lease_run_id == run_id:
                    room.status = "vacant"
                    room.contract_id = None
                    room.lead_id = None
                    room.lease_run_id = None
                    room.touch("purge")
                    released.append(room.id)
            for name, rows in self.tables.items():
                if name == "rooms":
                    continue
                doomed = [k for k, v in rows.items() if v.run_id == run_id]
                for k in doomed:
                    del rows[k]
                if doomed:
                    removed[name] = len(doomed)
            if released:
                removed["rooms_released"] = len(released)
            return removed

    @staticmethod
    def dump(entity: Entity) -> dict[str, Any]:
        return asdict(entity)


STORE = Store()
