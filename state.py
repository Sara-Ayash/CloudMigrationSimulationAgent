"""State management for the simulation."""

import uuid
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Set, Optional, Dict, Any

from config import CompletionConditions, config

# Canonical constraint names (must match parser.VALID_CONSTRAINTS)
_VALID_CONSTRAINTS = {"time", "cost", "security", "perf", "downtime", "partial_docs"}


@dataclass
class State:
    """Simulation state tracking."""
    session_id: str
    user_id: str
    scenario_variant: Optional[Dict[str, Any]] = None
    round_count: int = 0
    max_rounds: int = os.environ.get("SIMULATION_MAX_ROUNDS", 3)
    personas_triggered: Set[str] = field(default_factory=set)
    constraints_addressed: Set[str] = field(default_factory=set)
    strategy_selected: Optional[str] = None
    risk_flags: List[str] = field(default_factory=list)
    history: List[Dict[str, Any]] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    deadline_virtual: str = "T+2 weeks"
    last_persona: Optional[str] = None  # Track last persona to ensure variety
    in_final_review: bool = False  # Track if we're in the final review round
    weeks_left: int = 10
    budget_level: str = "low"  # "low" | "medium" | "high"
    downtime_budget_minutes: int = 5
    slo_availability: str = "99.9%"
    target_cost_reduction_pct: int = 30
    critical_dependencies: List[str] = field(default_factory=list)
    last_extracted: Dict[str, Any] = field(default_factory=dict)
    missing_deliverables: Set[str] = field(default_factory=set)  # e.g. {"timeline","rollback","cost"}
    risk_score: int = 0  # 0-100


    def should_end(self, completion_conditions: CompletionConditions) -> bool:
        """Check if simulation should end based on completion conditions."""
        # Safety cap: max rounds reached
        if self.round_count >= self.max_rounds:
            return True

        # Check if strategy is required but not selected
        if completion_conditions.REQUIRE_STRATEGY and self.strategy_selected is None:
            return False

        # Check minimum personas
        if len(self.personas_triggered) < completion_conditions.MIN_PERSONAS:
            return False

        # Check minimum constraints
        if len(self.constraints_addressed) < completion_conditions.MIN_CONSTRAINTS:
            return False

        # All conditions met
        return True

    def update_from_extracted(self, extracted: Dict[str, Any]) -> None:
        """Update state from extracted user response data."""
        # Update strategy if detected
        if extracted.get("strategy") is not None:
            self.strategy_selected = extracted["strategy"]

        # Update constraints (normalize to lowercase and only allow known keys)
        for constraint in extracted.get("constraints", []):
            if isinstance(constraint, str):
                key = constraint.strip().lower()
                if key in _VALID_CONSTRAINTS:
                    self.constraints_addressed.add(key)

        # Check for risk flags
        if self.strategy_selected == "rewrite" and "time" in self.constraints_addressed:
            risk_flag = "rewrite_conflicts_with_time_pressure"
            if risk_flag not in self.risk_flags:
                self.risk_flags.append(risk_flag)

        # Save last extracted for adaptive realism 
        self.last_extracted = extracted or {}

        # Compute missing deliverables (CTO realism: gate on missing essentials)
        missing = set()

        # These keys may or may not exist in your parser output yet.
        # If they don't exist, they'll default to missing -> which is OK for now.
        if not extracted.get("mentioned_timeline"):
            missing.add("timeline")
        if not extracted.get("mentioned_cost"):
            missing.add("cost")
        if not extracted.get("mentioned_rollback"):
            missing.add("rollback")
        if not extracted.get("mentioned_downtime_or_slo"):
            missing.add("downtime_slo")
        if not extracted.get("mentioned_tradeoff"):
            missing.add("tradeoff")

        self.missing_deliverables = missing

        # --- Risk scoring (simple, interpretable) ---
        risk = 0
        if "rollback" in missing:
            risk += 20
        if "timeline" in missing:
            risk += 10
        if self.strategy_selected in {"kubernetes", "multi_cloud"} and self.budget_level == "low":
            risk += 15
        if self.strategy_selected == "rewrite":
            risk += 15  # generally risky under time pressure

        self.risk_score = min(100, risk)


    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> None:
        """Add a message to history."""
        message = {
            "role": role,  # "user" or "agent"
            "content": content,
            "round": self.round_count,
            "timestamp": datetime.now().isoformat()
        }
        if metadata:
            message["metadata"] = metadata
        self.history.append(message)


def init_state(user_id: str) -> State:
    """Initialize a new simulation state."""
    s = State(
        session_id=str(uuid.uuid4()),
        user_id=user_id,
        max_rounds=config.max_rounds
    )

    # --- Real company baseline (feel free to tweak) ---
    s.weeks_left = 10
    s.budget_level = "low"
    s.downtime_budget_minutes = 5
    s.slo_availability = "99.9%"
    s.target_cost_reduction_pct = 30
    s.critical_dependencies = [
        "Data team reads directly from S3 (batch jobs depend on it)",
        "CloudWatch alarms are business-critical for on-call",
        "Legacy service uses AWS SDK v1 with partial documentation"
    ]

    return s

