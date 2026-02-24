"""Persona system for simulation interactions."""

import random
from typing import Dict, List, Optional, Any

from config import LLMConfig


class Persona:
    """Base persona class."""
    
    def __init__(self, name: str, role: str, llm_config: LLMConfig):
        """Initialize persona."""
        self.name = name
        self.role = role
        self.llm_config = llm_config
        self._client = None
    
    def _get_client(self):
        """Get LLM client (lazy initialization)."""
        if self._client is None:
            if self.llm_config.provider == "openai":
                try:
                    import openai
                    self._client = openai.OpenAI(api_key=self.llm_config.api_key)
                except ImportError:
                    raise ImportError("openai package not installed. Run: pip install openai")
            elif self.llm_config.provider == "anthropic":
                try:
                    import anthropic
                    self._client = anthropic.Anthropic(api_key=self.llm_config.api_key)
                except ImportError:
                    raise ImportError("anthropic package not installed. Run: pip install anthropic")
            else:
                raise ValueError(f"Unsupported LLM provider: {self.llm_config.provider}")
        return self._client
    
    def generate_complication(self, state: Any) -> str:
        """Generate a complication for this persona."""
        raise NotImplementedError
    
    def respond_as_persona(self, complication: str, state: Any, user_message: Optional[str] = None) -> str:
        """Generate a response as this persona. Requires LLM; no fallback."""
        return self._respond_with_llm(complication, state, user_message)
    
    def _respond_with_llm(self, complication: str, state: Any, user_message: Optional[str] = None) -> str:
        """Generate response using LLM."""
        client = self._get_client()

        # Build context (include more "company realism" if available in state)
        context_parts = [
            f"You are a {self.role} ({self.name}) in a cloud migration project.",
            f"Current situation: {complication}",
        ]

        if getattr(state, "scenario_variant", None):
            services = ", ".join(state.scenario_variant.get("services", []))
            if services:
                context_parts.append(f"The migration involves AWS services: {services}")

        if getattr(state, "strategy_selected", None):
            context_parts.append(f"The team is considering: {state.strategy_selected} strategy")

        if getattr(state, "constraints_addressed", None):
            constraints = ", ".join(state.constraints_addressed)
            if constraints:
                context_parts.append(f"Constraints already discussed: {constraints}")

        if not getattr(state, "info_gap_key", None):
             state.info_gap_key = random.choice(["baseline_cost", "peak_load", "downtime_budget", "slo_target"])

        # Optional realism fields (only if you added them to State)
        if hasattr(state, "weeks_left"):
            context_parts.append(f"Company constraint: {state.weeks_left} weeks left.")
        if hasattr(state, "budget_level"):
            context_parts.append(f"Company constraint: budget level is {state.budget_level}.")
        if hasattr(state, "downtime_budget_minutes"):
            context_parts.append(f"Company constraint: downtime budget is {state.downtime_budget_minutes} minutes.")
        if hasattr(state, "slo_availability"):
            context_parts.append(f"Company constraint: SLO availability target is {state.slo_availability}.")
        if hasattr(state, "target_cost_reduction_pct"):
            context_parts.append(f"Company constraint: target cost reduction is {state.target_cost_reduction_pct}%.")

        deps = getattr(state, "critical_dependencies", None)
        if deps:
            # Include 0-1 dependency to keep it readable
            idx = (hash(getattr(state, "user_id", "user")) + getattr(state, "round_count", 0)) % len(deps)
            context_parts.append(f"Known dependency: {deps[idx]}")

        missing = getattr(state, "missing_deliverables", None)
        if missing:
            missing_list = ", ".join(sorted(list(missing)))
            context_parts.append(f"Missing deliverables from user plan: {missing_list}")

        risk_score = getattr(state, "risk_score", None)
        if risk_score is not None:
            context_parts.append(f"Current risk score (0-100): {risk_score}")

        if user_message:
            context_parts.append(f"User's latest message: {user_message}")

        # Reveal ONE hidden constraint only on round 2, then keep reusing it
        rc = getattr(state, "round_count", 0)

        hidden_pool = [
            "New info: The nightly batch job runs with ConsistentRead=True on the DynamoDB table using partition key 'user_id'. Any migration that switches to eventual consistency or changes the partition key will cause incorrect financial aggregates.",
            "New info: The security team requires CloudTrail-equivalent audit logs for all read/write operations and documented key rotation policy (every 90 days) before approving any production cutover.",
            "New info: A legacy internal service assumes the IAM role name 'user-data-prod-role' and parses it explicitly in its configuration. Renaming or restructuring IAM roles will cause authentication failures in production.",
            "New info: A downstream analytics pipeline expects DynamoDB items to always include the attributes 'user_id', 'account_status', and 'created_at'. Removing or renaming any of these fields will break ETL ingestion jobs.",
        ]

        # Pick and store the hidden constraint only once (round 2)
        if rc == 2 and not getattr(state, "selected_hidden_constraint", None):
            state.selected_hidden_constraint = random.choice(hidden_pool)

        # Surface it from round 2 onward (same one), so the conversation can develop it
        if rc >= 2 and getattr(state, "selected_hidden_constraint", None):
            context_parts.append(state.selected_hidden_constraint)


        # --- Company constraints: choose 1 (max 2) based on user's answer/state ---
        def _pick_company_constraints(state: Any) -> List[str]:
            """
            Picks 1-2 constraints to surface this round, tied to what the user missed / chose.
            Uses state.missing_deliverables + strategy_selected + constraints_addressed.
            """
            missing = set(getattr(state, "missing_deliverables", set()) or [])
            addressed = set(getattr(state, "constraints_addressed", set()) or [])
            strategy = (getattr(state, "strategy_selected", None) or "").lower()

            # Candidate constraints with tags (so we can choose based on missing/strategy)
            candidates = []

            # timeline / time pressure
            if hasattr(state, "weeks_left"):
                candidates.append(("timeline", f"{state.weeks_left} weeks left until the deadline."))

            # cost / budget
            if hasattr(state, "budget_level"):
                candidates.append(("budget", f"Budget level is {state.budget_level}."))
            if hasattr(state, "target_cost_reduction_pct"):
                candidates.append(("cost_target", f"Cost reduction target is {state.target_cost_reduction_pct}%."))

            # reliability
            if hasattr(state, "downtime_budget_minutes"):
                candidates.append(("downtime", f"Downtime budget is {state.downtime_budget_minutes} minutes."))
            if hasattr(state, "slo_availability"):
                candidates.append(("slo", f"SLO availability target is {state.slo_availability}."))

            # dependencies (very realistic, but show sparingly)
            deps = getattr(state, "critical_dependencies", None)
            if deps:
                idx = (hash(getattr(state, "user_id", "user")) + getattr(state, "round_count", 0)) % len(deps)
                candidates.append(("dependency", f"Known dependency: {deps[idx]}"))

            # --- Priority rules: tie to user's answer ---
            priority_tags: List[str] = []

            # If user missed key deliverables, surface matching constraints first
            # (these names match what we suggested in state.update_from_extracted)
            if "timeline" in missing:
                priority_tags += ["timeline"]
            if "cost" in missing:
                priority_tags += ["budget", "cost_target"]
            if "downtime_slo" in missing:
                priority_tags += ["downtime", "slo"]
            if "rollback" in missing:
                # rollback isn't a "company constraint" line, but reliability constraints help push it
                priority_tags += ["downtime", "dependency"]
            if "tradeoff" in missing:
                priority_tags += ["timeline", "budget"]

            # Strategy-driven pressure (only if relevant)
            if "kubernetes" in strategy or "k8" in strategy:
                priority_tags += ["dependency", "slo", "downtime", "budget"]
            if "multi" in strategy:
                priority_tags += ["budget", "cost_target", "timeline"]
            if "rewrite" in strategy:
                priority_tags += ["timeline", "downtime"]
            if "adapter" in strategy or "abstraction" in strategy:
                priority_tags += ["dependency", "downtime"]

            # Avoid repeating the exact same constraint every round (simple memory)
            last_tags = set(getattr(state, "last_constraints_shown", set()) or [])

            # Score candidates: higher score => more likely to show
            scored = []
            for tag, text in candidates:
                score = 0
                if tag in priority_tags:
                    score += 3
                if tag not in last_tags:
                    score += 1
                # light preference: if already discussed "cost" constraint, don't spam cost every time
                if tag in ("budget", "cost_target") and "cost" in addressed:
                    score -= 1
                if tag in ("downtime", "slo") and "downtime" in addressed:
                    score -= 1
                scored.append((score, tag, text))

            scored.sort(reverse=True)  # highest score first
            

            # Pick the top candidate first
            chosen = []
            for score, tag, text in scored:
                if score < 0:
                    continue
                chosen.append((tag, text))
                break

            # Try to add a second constraint that creates a "tension" with the first one
            conflict_map = {
                "timeline": {"slo", "downtime"},
                "cost_target": {"slo", "downtime"},
                "budget": {"slo", "downtime"},
                "dependency": {"timeline", "downtime"},
            }

             
            if chosen:
                first_tag = chosen[0][0]

                conflict_set = conflict_map.get(first_tag, set())

                if conflict_set:
                    conflict_candidates = [
                        (tag, text)
                        for score, tag, text in scored
                        if score > 0 and tag != first_tag and tag in conflict_set
                    ]

                    if conflict_candidates:
                        tag, text = random.choice(conflict_candidates)
                        chosen.append((tag, text))


            # Persist what we showed to reduce repetition
            try:
                state.last_constraints_shown = {t for t, _ in chosen}
            except Exception:
                pass

            # Return 1-2 constraints (2 only if we found a conflicting one)
            return [txt for _, txt in chosen[:2]]



        picked_constraints = _pick_company_constraints(state)
        for c in picked_constraints[:2]:
            context_parts.append(f"Company constraint (relevant now): {c}")

        # Add hidden constraint as active constraint if exists
        if rc >= 2 and getattr(state, "selected_hidden_constraint", None):
            picked_constraints.append(state.selected_hidden_constraint)


        if not getattr(state, "info_gap_text", None):
            gap_options = [
                "Information gap: we do NOT have the current AWS monthly cost baseline yet.",
                "Information gap: we do NOT have peak load numbers (RCU/WCU/RPS) yet.",
                "Information gap: the downtime budget is not confirmed yet.",
                "Information gap: Do NOT assume any SLO number (99.9/99.95/etc.) until it is confirmed.",
            ]
            state.info_gap_text = random.choice(gap_options)

        # Show it in context AND in active constraints so the persona must address it
        context_parts.append(state.info_gap_text)
        if state.info_gap_text not in picked_constraints:
            picked_constraints.append(state.info_gap_text)

        
        # Add organizational politics 
        if not getattr(state, "org_pressure_text", None):
            org_pressures = [
                "Organizational pressure: The CFO has publicly committed to a 30% cost reduction this quarter.",
                "Organizational pressure: The Security Director has warned that no migration will be approved without full audit evidence.",
                "Organizational pressure: The VP Engineering prefers a rewrite instead of lift-and-shift.",
                "Organizational pressure: Product is concerned about customer churn if downtime exceeds expectations.",
            ]
            state.org_pressure_text = random.choice(org_pressures)

        context_parts.append(state.org_pressure_text)
        picked_constraints.append(state.org_pressure_text)


        context = "\n".join(context_parts)

        # --- Base rules for ALL personas (pressure + realism) ---
        base_rules = """
        Global rules (apply to ALL personas):
        - Do NOT give generic advice. Ground your response strictly in the provided context and the constraints surfaced this round.
        - If the user's plan lacks clarity or contains risk, ask up to 2-3 pointed follow-up questions that require concrete specifics (numbers, ownership, thresholds, assumptions).
        - Reference relevant concrete facts from the context (e.g., deadline, budget, SLO, dependency, selected strategy) when they materially impact the discussion.
        - Challenge assumptions only when they affect cost, reliability, timeline, security, or operational risk.
        - Always drive the conversation toward a decision, trade-off, or clarification.
        - End with one clear next action that moves the plan forward.
        - You may only reference the “Active constraints” listed below. Do not introduce or imply additional constraints.
        - If an "Information gap" is present, ask for it before giving a detailed plan.
        - If an Information gap blocks cost or reliability validation, you must pause approval until it is clarified.
        - Do not introduce new services or dependencies that are not mentioned in the context.

        Output style:
        - Write in natural conversational format (no bullet points).
        - Integrate follow-up questions smoothly into the dialogue (do not make them feel like a checklist).
        - Keep the tone aligned with the persona (CTO, PM, DevOps, etc.).
        - Conclude with a clear forward-driving sentence that naturally states what must happen next, without labeling it explicitly.
         """

        # --- Style + role focus (different "voice" per persona) ---
        role = (self.role or "").lower()

        style = ""
        role_focus = ""

        if role == "cto":
            style = """
    Style:
    - Very concise, executive tone. Slightly stressful but professional.
    - No long explanations. Prefer short sentences and direct questions.
    """
            role_focus = """
    CTO focus:
    - Force a trade-off decision (what you will sacrifice to meet constraints).
    - Demand ownership and rollback: who is on-call, cutover/rollback trigger.
    - Push on cost and long-term maintainability; ask for KPI tracking.
    - If rollback/timeline/cost are missing, block approval explicitly.
    """
        elif role == "product manager":
            style = """
    Style:
    - Crisp and pragmatic. Customer/stakeholder oriented. Slight urgency.
    - Push for clarity and prioritization; avoid technical deep-dives unless needed.
    """
            role_focus = """
    PM focus:
    - Push on scope, milestones, and customer impact.
    - Force prioritization: what will NOT ship now.
    - Ask for a weekly plan (milestones) and stakeholder communication plan.
    - If timeline is unclear, request a phased plan with dates/milestones.
    """
        elif role == "devops engineer":
            style = """
    Style:
    - Technical and risk-aware. Calm but firm.
    - Uses operational language (runbook, blast radius, staging, observability).
    """
            role_focus = """
    DevOps focus:
    - Push on deployment safety, IAM mapping, observability, CI/CD, and incident response.
    - Require a runbook: monitoring, alerting, rollback steps.
    - Ask about testing/staging strategy and minimizing blast radius.
    - If security/downtime is not addressed, escalate the risk.
    """
        else:
            style = """
    Style:
    - Professional and direct.
    """
            role_focus = """
    Role focus:
    - Ask for assumptions, risks, and measurable next steps relevant to your role.
    """
       
        escalation_note = ""

        risk_score = getattr(state, "risk_score", None)
        if risk_score is not None:
            if risk_score >= 75:
                escalation_note = """
        Risk level is very high. Be firm and urgent. Do not approve a cutover plan until the user provides
        clear owners, concrete rollback triggers, and measurable thresholds. Keep the tone professional and forward-moving.
        """
            elif risk_score >= 50:
                escalation_note = """
        Risk level is elevated. Ask for concrete numbers and owners, and push for clear trade-offs and KPIs.
        """

        active_constraints = picked_constraints or []

        prompt = f"""{context}

        Active constraints this round:
        - """ + "\n- ".join(active_constraints) + f"""

    Respond as {self.name} ({self.role}). Be professional and realistic.
    {base_rules}
    {style}
    {role_focus}
    {escalation_note}
    """

        if self.llm_config.provider == "openai":
            response = client.chat.completions.create(
                model=self.llm_config.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are {self.name}, a {self.role}. "
                            "You are participating in a realistic cloud-migration simulation. "
                            "Follow the user's provided context and the rules in the prompt."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=self.llm_config.temperature,
                max_tokens=self.llm_config.max_tokens,
            )
            return response.choices[0].message.content.strip()
        else:  # anthropic
            response = client.messages.create(
                model=self.llm_config.model,
                max_tokens=self.llm_config.max_tokens,
                temperature=self.llm_config.temperature,
                messages=[
                    {"role": "user", "content": prompt},
                ],
            )
            return response.content[0].text.strip()


    def _respond_template(self, complication: str, state: Any) -> str:
        """Fallback template-based response."""
        return f"[{self.name} ({self.role})]: {complication}"


class PMPersona(Persona):
    """Product Manager persona."""
    
    def __init__(self, llm_config: LLMConfig):
        """Initialize PM persona."""
        super().__init__("Sarah", "Product Manager", llm_config)
    
    def generate_complication(self, state: Any) -> str:
        """Generate PM complication."""
        complications = [
            "Deadline shortened: we must ship in 10 days. No full refactor is possible.",
            "Stakeholders want to see progress this week. Can we show something working quickly?",
            "The scope has changed - we need to support 3x more users than originally planned.",
            "Upper management is asking for daily updates. We need a clear migration timeline.",
            "Customer commitments require zero disruption. How do we ensure smooth transition?"
        ]
        return random.choice(complications)
    
    def _respond_template(self, complication: str, state: Any) -> str:
        """Template response for PM."""
        return f"{complication} We need to balance speed with quality. What's the fastest path that doesn't compromise our users?"


class DevOpsPersona(Persona):
    """DevOps Engineer persona."""
    
    def __init__(self, llm_config: LLMConfig):
        """Initialize DevOps persona."""
        super().__init__("Alex", "DevOps Engineer", llm_config)
    
    def generate_complication(self, state: Any) -> str:
        """Generate DevOps complication."""
        complications = [
            "Access model changes: IAM roles need to map to Azure RBAC. We must pass security review before deployment.",
            "Infrastructure as Code needs to be rewritten. Our Terraform modules are AWS-specific.",
            "Monitoring and logging systems are different. We need a migration plan for observability.",
            "CI/CD pipelines depend on AWS-specific services. We'll need to rebuild them.",
            "Network security groups and VPC configurations don't translate directly. This affects our architecture."
        ]
        return random.choice(complications)
    
    def _respond_template(self, complication: str, state: Any) -> str:
        """Template response for DevOps."""
        return f"{complication} Security and infrastructure concerns are critical. We need to ensure nothing breaks during migration."


class CTOPersona(Persona):
    """CTO persona."""
    
    def __init__(self, llm_config: LLMConfig):
        """Initialize CTO persona."""
        super().__init__("Michael", "CTO", llm_config)
    
    def generate_complication(self, state: Any) -> str:
        """Generate CTO complication."""
        complications = [
            "Cost cap added: we have a strict budget. Egress costs and new managed services need careful evaluation.",
            "Long-term strategy: we're considering multi-cloud. How does this migration fit our 5-year plan?",
            "Vendor lock-in is a concern. We want to avoid being tied to one provider's proprietary features.",
            "Team expertise: our engineers know AWS well. Training costs and time for new cloud provider need consideration.",
            "Compliance requirements: we need to ensure the new provider meets all regulatory standards."
        ]
        return random.choice(complications)
    
    def _respond_template(self, complication: str, state: Any) -> str:
        """Template response for CTO."""
        return f"{complication} We need to think strategically about costs, long-term maintainability, and business alignment."


def choose_next_persona(state: Any) -> str:
    """
    Choose which persona should appear next.
    
    Strategy:
    1. Always choose a different persona from the last one (ensures variety)
    2. Prioritize personas matching missing constraints
    3. Rotate through all available personas to ensure diversity
    """
    available = ["PM", "DevOps", "CTO"]
    last_persona = state.last_persona
    
    # Exclude last persona to ensure variety (never repeat consecutive)
    candidates = [p for p in available if p != last_persona]
    
    # If this is the first round, choose randomly or based on constraints
    if not last_persona:
        # Map constraints to personas
        constraint_to_persona = {
            "security": "DevOps",
            "cost": "CTO",
            "time": "PM"
        }
        
        # Check for missing constraints
        for constraint, persona in constraint_to_persona.items():
            if constraint not in state.constraints_addressed:
                return persona
        
        # No missing constraints - start with first available
        return available[0]
    
    # Not first round - ensure we pick someone different
    if len(candidates) == 1:
        return candidates[0]
    
    # Map constraints to personas
    constraint_to_persona = {
        "security": "DevOps",
        "cost": "CTO",
        "time": "PM"
    }
    
    # Find candidates that match missing constraints
    matching_personas = []
    for constraint, persona in constraint_to_persona.items():
        if constraint not in state.constraints_addressed and persona in candidates:
            matching_personas.append(persona)
    
    # If we have personas matching missing constraints, prefer them
    if matching_personas:
        # Use round number to alternate between matching personas
        return matching_personas[state.round_count % len(matching_personas)]
    
    # No matching constraints - rotate through all candidates
    # Use round number to cycle through, ensuring we don't repeat last
    # This creates variety: if last was PM, next could be DevOps or CTO
    return candidates[state.round_count % len(candidates)]


def get_persona_instance(persona_name: str, llm_config: LLMConfig) -> Persona:
    """Get persona instance by name."""
    if persona_name == "PM":
        return PMPersona(llm_config)
    elif persona_name == "DevOps":
        return DevOpsPersona(llm_config)
    elif persona_name == "CTO":
        return CTOPersona(llm_config)
    else:
        raise ValueError(f"Unknown persona: {persona_name}")


def generate_complication(state: Any, persona: Persona) -> str:
    """
    Generate a complication that feels like a real company:
    - Always includes baseline constraints (deadline/budget/SLO/deps)
    - Adapts to what the user did NOT provide (missing_deliverables)
    - Adapts to chosen strategy (strategy_selected)
    """
    # --- 1) Baseline "company reality" (comes from state.py you added) ---
    baseline_lines = []
    if hasattr(state, "weeks_left"):
        baseline_lines.append(f"Timeline: {state.weeks_left} weeks left.")
    if hasattr(state, "budget_level"):
        baseline_lines.append(f"Budget level: {state.budget_level}.")
    if hasattr(state, "downtime_budget_minutes"):
        baseline_lines.append(f"Downtime budget: {state.downtime_budget_minutes} minutes.")
    if hasattr(state, "slo_availability"):
        baseline_lines.append(f"SLO availability target: {state.slo_availability}.")
    if hasattr(state, "target_cost_reduction_pct"):
        baseline_lines.append(f"Cost target: reduce by {state.target_cost_reduction_pct}%.")

    # dependencies (very realistic)
    deps = getattr(state, "critical_dependencies", None)
    if deps:
        # include 1 dependency per round to avoid overload
        idx = (hash(state.user_id) + state.round_count) % len(deps)
        baseline_lines.append(f"Known dependency: {deps[idx]}")

    baseline = " ".join(baseline_lines).strip()

    # --- 2) Adaptation: what user missed (CTO gate style) ---
    missing = list(getattr(state, "missing_deliverables", set()) or [])
    strategy = getattr(state, "strategy_selected", None) or "unspecified"

    # If key info missing, create a "gate" complication (especially for CTO)
    if missing and persona.role.lower() == "cto":
        # keep it sharp and stressful
        needed = ", ".join(missing[:4])
        return (
            f"{baseline}\n"
            f"User plan is still too high-level. Missing: {needed}.\n"
            "As CTO, you must not approve until these are addressed with concrete numbers and a rollback plan."
        )

    # --- 3) Adaptation: strategy-specific realistic pressure ---
    strategy_pressure = ""
    s = strategy.lower()
    if "kubernetes" in s or "k8" in s:
        strategy_pressure = (
            "Proposed direction includes Kubernetes/containerization. "
            "Security and ops ownership are now critical: image signing, cluster maintenance, on-call, and cost."
        )
    elif "multi" in s:
        strategy_pressure = (
            "Multi-cloud was mentioned. This may double complexity. "
            "You must justify why we need multi-cloud now and define measurable benefits."
        )
    elif "rewrite" in s:
        strategy_pressure = (
            "Rewrite is risky under time pressure. "
            "We need a phased approach or a smaller slice to migrate first, with clear milestones."
        )
    elif "adapter" in s or "abstraction" in s:
        strategy_pressure = (
            "Adapter/abstraction layer sounds reasonable, but hidden dependencies may bypass it. "
            "We need a plan to find and mitigate direct AWS SDK usage."
        )

    # --- 4) Occasional twist (company chaos) every 2nd round ---
    twist = ""
    if state.round_count % 2 == 0:
        twists = [
            "New info: Security blocks new deployments this week unless risk is low.",
            "Incident: a production alert fired; leadership wants zero risky changes for 48 hours.",
            "Customer pressure: enterprise client reports latency regression; +10ms max allowed.",
            "Hidden dependency discovered: a legacy service calls AWS SDK directly with no tests."
        ]
        twist = twists[(hash(state.user_id) + state.round_count) % len(twists)]

    # Fallback to persona's own complication, but enriched
    persona_comp = persona.generate_complication(state)
    parts = [p for p in [baseline, strategy_pressure, twist, persona_comp] if p]
    return "\n".join(parts)
