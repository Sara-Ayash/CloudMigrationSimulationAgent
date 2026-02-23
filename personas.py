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
        
        # Build context
        context_parts = [
            f"You are a {self.role} ({self.name}) in a cloud migration project.",
            f"Current situation: {complication}",
        ]
        
        if state.scenario_variant:
            services = ", ".join(state.scenario_variant.get("services", []))
            context_parts.append(f"The migration involves AWS services: {services}")
        
        if state.strategy_selected:
            context_parts.append(f"The team is considering: {state.strategy_selected} strategy")
        
        if state.constraints_addressed:
            constraints = ", ".join(state.constraints_addressed)
            context_parts.append(f"Constraints already discussed: {constraints}")
        
        if user_message:
            context_parts.append(f"User's latest message: {user_message}")
        
        context = "\n".join(context_parts)
        
        prompt = f"""{context}

Respond as {self.name} ({self.role}). Be concise, professional, and focused on your role's concerns. 
Your response should be 2-4 sentences, addressing the complication and your perspective on the migration."""
        
        if self.llm_config.provider == "openai":
            response = client.chat.completions.create(
                model=self.llm_config.model,
                messages=[
                    {"role": "system", "content": f"You are {self.name}, a {self.role}. Respond naturally and professionally."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.llm_config.temperature,
                max_tokens=self.llm_config.max_tokens
            )
            return response.choices[0].message.content.strip()
        else:  # anthropic
            response = client.messages.create(
                model=self.llm_config.model,
                max_tokens=self.llm_config.max_tokens,
                temperature=self.llm_config.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
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
    """Generate a complication for the given persona."""
    return persona.generate_complication(state)
