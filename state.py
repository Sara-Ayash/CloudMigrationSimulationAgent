"""State management for the simulation."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Set, Optional, Dict, Any

from config import CompletionConditions, config


@dataclass
class State:
    """Simulation state tracking."""
    session_id: str
    user_id: str
    scenario_variant: Optional[Dict[str, Any]] = None
    round_count: int = 0
    max_rounds: int = 8
    personas_triggered: Set[str] = field(default_factory=set)
    constraints_addressed: Set[str] = field(default_factory=set)
    strategy_selected: Optional[str] = None
    risk_flags: List[str] = field(default_factory=list)
    history: List[Dict[str, Any]] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    deadline_virtual: str = "T+2 weeks"
    last_persona: Optional[str] = None  # Track last persona to ensure variety
    in_final_review: bool = False  # Track if we're in the final review round

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

        # Update constraints
        for constraint in extracted.get("constraints", []):
            self.constraints_addressed.add(constraint)

        # Check for risk flags
        if self.strategy_selected == "rewrite" and "time" in self.constraints_addressed:
            risk_flag = "rewrite_conflicts_with_time_pressure"
            if risk_flag not in self.risk_flags:
                self.risk_flags.append(risk_flag)

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
    return State(
        session_id=str(uuid.uuid4()),
        user_id=user_id,
        max_rounds=config.max_rounds
    )
