"""Evaluation engine for simulation sessions."""

from typing import Dict, List, Any
from dataclasses import dataclass

from state import State


@dataclass
class EvaluationReport:
    """Evaluation report structure."""
    score: int
    strategy: str
    personas_used: List[str]
    constraints_covered: List[str]
    strengths: List[str]
    gaps: List[str]
    recommendations: List[str]


def evaluate_session(state: State) -> EvaluationReport:
    """Evaluate the simulation session and generate a report."""
    score = 0
    notes = []
    
    # Strategy scoring
    if state.strategy_selected in ["adapter_layer", "abstraction", "hybrid"]:
        score += 2
        notes.append("Chose migration-friendly strategy")
    elif state.strategy_selected == "rewrite":
        score += 1
        notes.append("Chose rewrite strategy (higher risk)")
    
    # Constraint coverage scoring
    if "downtime" in state.constraints_addressed:
        score += 2
        notes.append("Considered availability / downtime")
    
    if "security" in state.constraints_addressed:
        score += 2
        notes.append("Considered security implications")
    
    if "cost" in state.constraints_addressed:
        score += 1
        notes.append("Considered cost implications")
    
    if "perf" in state.constraints_addressed:
        score += 1
        notes.append("Considered performance under load")
    
    if "time" in state.constraints_addressed:
        score += 1
        notes.append("Considered time constraints")
    
    if "partial_docs" in state.constraints_addressed:
        score += 1
        notes.append("Considered documentation gaps")
    
    # Penalties for risk flags
    if "rewrite_conflicts_with_time_pressure" in state.risk_flags:
        score -= 2
        notes.append("⚠️ Rewrite conflicts with stated time constraints")
    
    # Clamp score to 0-10
    score = max(0, min(10, score))
    
    # Extract strengths
    strengths = extract_strengths(notes, state)
    
    # Detect gaps
    gaps = detect_gaps(state)
    
    # Generate recommendations
    recommendations = generate_recommendations(gaps, state)
    
    return EvaluationReport(
        score=score,
        strategy=state.strategy_selected or "None selected",
        personas_used=list(state.personas_triggered),
        constraints_covered=list(state.constraints_addressed),
        strengths=strengths,
        gaps=gaps,
        recommendations=recommendations
    )


def extract_strengths(notes: List[str], state: State) -> List[str]:
    """Extract strengths from evaluation notes."""
    strengths = []
    
    # Positive notes (excluding penalties)
    positive_notes = [n for n in notes if "⚠️" not in n]
    strengths.extend(positive_notes)
    
    # Additional strengths based on state
    if len(state.personas_triggered) >= 3:
        strengths.append("Engaged with multiple stakeholders")
    
    if len(state.constraints_addressed) >= 4:
        strengths.append("Comprehensive constraint analysis")
    
    if state.strategy_selected:
        strengths.append("Made a clear strategic decision")
    
    return strengths if strengths else ["Participated in the simulation"]


def detect_gaps(state: State) -> List[str]:
    """Detect gaps in the user's reasoning."""
    gaps = []
    
    # Missing common constraints (show with display names)
    common_constraints = ["time", "cost", "security", "downtime"]
    missing = [c for c in common_constraints if c not in state.constraints_addressed]
    if missing:
        labels = [CONSTRAINT_DISPLAY_NAMES.get(c, c.replace("_", " ").title()) for c in missing]
        gaps.append("Did not address: " + ", ".join(labels))
    
    # Missing strategy
    if not state.strategy_selected:
        gaps.append("No clear migration strategy selected")
    
    # Missing personas
    if len(state.personas_triggered) < 2:
        gaps.append("Limited stakeholder engagement")
    
    # Risk flags indicate gaps (show human-readable text in report)
    _RISK_FLAG_LABELS = {
        "rewrite_conflicts_with_time_pressure": "Rewrite strategy conflicts with stated time pressure",
    }
    if state.risk_flags:
        labels = [_RISK_FLAG_LABELS.get(flag, flag.replace("_", " ")) for flag in state.risk_flags]
        gaps.append("Risk conflicts detected: " + "; ".join(labels))
    
    # Common missing considerations
    missing_considerations = []
    if "monitoring" not in str(state.history).lower():
        missing_considerations.append("monitoring/observability")
    if "rollback" not in str(state.history).lower() and "roll back" not in str(state.history).lower():
        missing_considerations.append("rollback strategy")
    if "testing" not in str(state.history).lower():
        missing_considerations.append("testing approach")
    
    if missing_considerations:
        gaps.append(f"Did not discuss: {', '.join(missing_considerations)}")
    
    return gaps if gaps else ["No major gaps detected"]


def generate_recommendations(gaps: List[str], state: State) -> List[str]:
    """Generate recommendations based on gaps."""
    recommendations = []
    
    # Strategy recommendations
    if not state.strategy_selected:
        recommendations.append("Consider choosing a clear migration strategy (adapter layer, abstraction, hybrid, or rewrite)")
    
    # Constraint recommendations
    if "time" not in state.constraints_addressed:
        recommendations.append("Consider time constraints and deadlines in your planning")
    
    if "cost" not in state.constraints_addressed:
        recommendations.append("Evaluate cost implications of different migration approaches")
    
    if "security" not in state.constraints_addressed:
        recommendations.append("Address security and compliance requirements early")
    
    if "downtime" not in state.constraints_addressed:
        recommendations.append("Plan for zero-downtime migration strategies")
    
    # General recommendations
    if len(state.personas_triggered) < 3:
        recommendations.append("Engage with more stakeholders (PM, DevOps, CTO) to get diverse perspectives")
    
    if "monitoring" in str(gaps).lower():
        recommendations.append("Plan for monitoring and observability in the new cloud environment")
    
    if "rollback" in str(gaps).lower():
        recommendations.append("Develop a rollback strategy in case migration issues arise")
    
    if "testing" in str(gaps).lower():
        recommendations.append("Define testing strategy for migrated services")
    
    # Risk mitigation
    if state.risk_flags:
        recommendations.append("Reconcile conflicting requirements (e.g., rewrite vs. time pressure)")
    
    return recommendations if recommendations else ["Continue practicing migration planning scenarios"]


def format_final_review_message(state: State) -> str:
    """Format a final review message asking user about their final strategy and showing gaps."""
    gaps = detect_gaps(state)
    recommendations = generate_recommendations(gaps, state)
    
    strategy_display = (state.strategy_selected or "Not selected").replace("_", " ").title()
    constraints_display = _display_constraints(list(state.constraints_addressed))
    message = f"""
## Final review round

Before we conclude, let's review your migration strategy:

- **Strategy:** {strategy_display}
- **Constraints addressed:** {constraints_display}

"""
    
    if gaps and len(gaps) > 0 and gaps[0] != "No major gaps detected":
        message += "**⚠️  Potential Gaps to Consider:**\n"
        for i, gap in enumerate(gaps, 1):
            message += f"  {i}. {gap}\n"
        message += "\n"
    
    if recommendations and len(recommendations) > 0:
        message += "**💡  Recommendations to Improve:**\n"
        for i, rec in enumerate(recommendations, 1):
            message += f"  {i}. {rec}\n"
        message += "\n"
    
    message += """## Question: ##\n
**Is this your final migration strategy?**

If you'd like to refine your approach based on the gaps and recommendations above, please share your updated strategy or any additional considerations.

Type your response to confirm or update your strategy...
"""
    
    return message


def explain_score(state: State, report: EvaluationReport) -> str:
    """Generate detailed explanation of the score and what's missing."""
    explanation = "\n**Score breakdown** (max 10 points)\n\n"
    
    # Strategy points
    if state.strategy_selected in ["adapter_layer", "abstraction", "hybrid"]:
        explanation += f"- Strategy: **2/2** (chose {state.strategy_selected.replace('_', ' ')})\n"
    elif state.strategy_selected == "rewrite":
        explanation += "- Strategy: **1/2** (rewrite — higher risk)\n"
    else:
        explanation += "- Strategy: **0/2** (not selected)\n"
    
    constraint_points = {
        "downtime": (2, "Downtime / availability"),
        "security": (2, "Security / compliance"),
        "cost": (1, "Cost / budget"),
        "perf": (1, "Performance / scalability"),
        "time": (1, "Time / deadlines"),
        "partial_docs": (1, "Documentation gaps")
    }
    
    for constraint, (points, display_name) in constraint_points.items():
        if constraint in state.constraints_addressed:
            explanation += f"- {display_name}: **{points}/{points}**\n"
        else:
            explanation += f"- {display_name}: **0/{points}**\n"
    
    if state.risk_flags:
        explanation += "\n- Risk penalties: **-2** (conflicting choices)\n"
    
    explanation += f"\n**Total: {report.score}/10**\n"
    
    missing_points = 10 - report.score
    if missing_points > 0:
        explanation += f"\n**How to improve** (+{missing_points} point(s) to reach 10/10)\n\n"
        tips = []
        if not state.strategy_selected:
            tips.append("Select a migration strategy (adapter layer, abstraction, hybrid, or rewrite)")
        for constraint in constraint_points:
            if constraint not in state.constraints_addressed:
                _, display_name = constraint_points[constraint]
                tips.append(f"Address {display_name.lower()}")
        if state.risk_flags:
            tips.append("Resolve conflicting requirements (e.g. rewrite vs. time pressure)")
        for t in tips:
            explanation += f"- {t}\n"
    else:
        explanation += "\nAll key aspects covered.\n"
    
    return explanation


# Human-readable labels for constraints (no abbreviations in reports)
CONSTRAINT_DISPLAY_NAMES = {
    "time": "Time",
    "cost": "Cost",
    "security": "Security",
    "perf": "Performance",
    "downtime": "Downtime / availability",
    "partial_docs": "Documentation",
}


def _display_strategy(raw: str) -> str:
    """Human-friendly strategy label; never show 'None'."""
    if not raw or raw == "None selected" or str(raw).strip().lower() == "none":
        return "—"
    return raw.replace("_", " ").strip().title()


def _display_constraints(constraints_list: list) -> str:
    """Human-friendly constraints list with full names."""
    if not constraints_list:
        return "—"
    return ", ".join(CONSTRAINT_DISPLAY_NAMES.get(c, c.replace("_", " ").title()) for c in constraints_list)


def _display_list(items: list, empty_label: str = "—") -> str:
    """Human-friendly list; never show 'None'."""
    if not items:
        return empty_label
    return ", ".join(str(x) for x in items)


def format_feedback(report: EvaluationReport, state: State) -> str:
    """Format evaluation report as human-readable feedback."""
    strategy_text = _display_strategy(report.strategy)
    personas_text = _display_list(report.personas_used)
    constraints_text = _display_constraints(report.constraints_covered)

    feedback = """
---

## Simulation finished

**Summary**

| | |
|---|---|
| **Strategy** | """ + strategy_text + """ |
| **Personas encountered** | """ + personas_text + """ |
| **Constraints covered** | """ + constraints_text + """ |
| **Score** | """ + str(report.score) + """/10 |

"""
    feedback += explain_score(state, report)
    feedback += "\n**Strengths**\n\n"
    for strength in report.strengths:
        line = strength.strip()
        if line:
            feedback += f"- {line}\n"
    feedback += "\n---\n"
    return feedback
