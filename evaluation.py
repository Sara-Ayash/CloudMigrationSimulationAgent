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
    
    # Missing common constraints
    common_constraints = ["time", "cost", "security", "downtime"]
    missing = [c for c in common_constraints if c not in state.constraints_addressed]
    if missing:
        gaps.append(f"Did not address: {', '.join(missing)}")
    
    # Missing strategy
    if not state.strategy_selected:
        gaps.append("No clear migration strategy selected")
    
    # Missing personas
    if len(state.personas_triggered) < 2:
        gaps.append("Limited stakeholder engagement")
    
    # Risk flags indicate gaps
    if state.risk_flags:
        gaps.append(f"Risk conflicts detected: {', '.join(state.risk_flags)}")
    
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
    
    message = f"""
{'='*60}
📋 Final Review Round
{'='*60}

Before we conclude, let's review your migration strategy:

**Current Strategy:** {state.strategy_selected if state.strategy_selected else "Not yet selected"}

**Constraints Addressed:** {', '.join(state.constraints_addressed) if state.constraints_addressed else "None"}

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
    
    message += """**Question:**
Is this your final migration strategy? 

If you'd like to refine your approach based on the gaps and recommendations above, please share your updated strategy or any additional considerations.

Type your response to confirm or update your strategy...
"""
    
    return message


def explain_score(state: State, report: EvaluationReport) -> str:
    """Generate detailed explanation of the score and what's missing."""
    explanation = "\n📊 Score Breakdown:\n"
    explanation += "   (Maximum possible: 10 points)\n\n"
    
    # Strategy points
    if state.strategy_selected in ["adapter_layer", "abstraction", "hybrid"]:
        explanation += f"   ✓ Strategy selection: 2/2 points ✓ (chose {state.strategy_selected})\n"
    elif state.strategy_selected == "rewrite":
        explanation += f"   ✓ Strategy selection: 1/2 points (chose rewrite strategy - higher risk)\n"
    else:
        explanation += f"   ✗ Strategy selection: 0/2 points (no strategy selected)\n"
    
    # Constraint points with display names
    constraint_points = {
        "downtime": (2, "Downtime / Availability"),
        "security": (2, "Security / Compliance"),
        "cost": (1, "Cost / Budget"),
        "perf": (1, "Performance / Scalability"),
        "time": (1, "Time / Deadlines"),
        "partial_docs": (1, "Incomplete / Missing Documentation")
    }
    
    explanation += "\n   Constraint Coverage:\n"
    for constraint, (points, display_name) in constraint_points.items():
        if constraint in state.constraints_addressed:
            explanation += f"   ✓ {display_name}: {points}/{points} points ✓\n"
        else:
            explanation += f"   ✗ {display_name}: 0/{points} points (not addressed)\n"
    
    # Penalties
    if state.risk_flags:
        penalty = 2
        explanation += f"\n   ⚠️  Risk penalties: -{penalty} points (conflicting choices)\n"
    
    # Show total score
    explanation += f"\n   📊 Total Score: {report.score}/10 points\n"
    
    # Calculate what's missing
    max_points = 10
    current_score = report.score
    missing_points = max_points - current_score
    
    if missing_points > 0:
        explanation += f"\n   📉 Missing: {missing_points} point(s) to reach perfect score (10/10)\n"
        explanation += "   To improve your score:\n"
        
        if not state.strategy_selected:
            explanation += "     • Select a migration strategy (adapter_layer, abstraction, hybrid, or rewrite) [+2 points]\n"
        
        missing_constraints = [c for c in constraint_points.keys() if c not in state.constraints_addressed]
        if missing_constraints:
            for constraint in missing_constraints:
                points, display_name = constraint_points[constraint]
                # Make messages more descriptive
                if constraint == "partial_docs":
                    explanation += f"     • Consider challenges with incomplete/missing documentation (+{points} point(s))\n"
                elif constraint == "downtime":
                    explanation += f"     • Address downtime and availability concerns (+{points} point(s))\n"
                elif constraint == "security":
                    explanation += f"     • Address security and compliance requirements (+{points} point(s))\n"
                elif constraint == "cost":
                    explanation += f"     • Consider cost and budget implications (+{points} point(s))\n"
                elif constraint == "perf":
                    explanation += f"     • Address performance and scalability needs (+{points} point(s))\n"
                elif constraint == "time":
                    explanation += f"     • Consider time constraints and deadlines (+{points} point(s))\n"
                else:
                    explanation += f"     • Address {display_name.lower()} (+{points} point(s))\n"
        
        if state.risk_flags:
            explanation += "     • Resolve conflicting requirements (e.g., rewrite vs. time pressure) [+2 points]\n"
    else:
        explanation += f"\n   🎉 Perfect score! All key aspects covered.\n"
    
    return explanation


def format_feedback(report: EvaluationReport, state: State) -> str:
    """Format evaluation report as human-readable feedback."""
    feedback = f"""
{'='*60}
Simulation Finished ✅
{'='*60}

Summary:
  • Strategy: {report.strategy}
  • Personas encountered: {', '.join(report.personas_used) if report.personas_used else 'None'}
  • Constraints covered: {', '.join(report.constraints_covered) if report.constraints_covered else 'None'}
  • Score (reasoning quality): {report.score}/10
"""
    
    # Add detailed score explanation
    feedback += explain_score(state, report)
    
    feedback += "\nStrengths:\n"
    for strength in report.strengths:
        feedback += f"  ✓ {strength}\n"
    
    feedback += "\n" + "="*60 + "\n"
    
    return feedback
