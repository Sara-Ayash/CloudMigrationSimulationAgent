"""User response parsing using LLM API."""

import json
from typing import Dict, List, Any

from config import LLMConfig

# Canonical constraint names used everywhere (evaluation, state, UI)
VALID_CONSTRAINTS = {"time", "cost", "security", "perf", "downtime", "partial_docs"}


def _normalize_constraints(raw: Any) -> List[str]:
    """Normalize constraint list: lowercase, filter to valid names only."""
    if not raw:
        return []
    result = []
    for c in raw if isinstance(raw, list) else []:
        if isinstance(c, str):
            key = c.strip().lower()
            if key in VALID_CONSTRAINTS:
                result.append(key)
    return result


class UserResponseParser:
    """Parse user responses to extract strategy, constraints, and confidence."""
    
    def __init__(self, llm_config: LLMConfig):
        """Initialize parser with LLM configuration."""
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
    
    def parse_user_response(self, user_message: str) -> Dict[str, Any]:
        """Parse user message to extract strategy, constraints, and confidence. Requires LLM; no fallback."""
        return self._parse_with_llm(user_message)
    
    def _parse_with_llm(self, user_message: str) -> Dict[str, Any]:
        """Parse using LLM API."""
        client = self._get_client()
        
        prompt = f"""Analyze the following user message about cloud migration and extract structured information.

User message: "{user_message}"

Extract:
1. Strategy mentioned (one of: "adapter_layer", "abstraction", "hybrid", "rewrite", or null if none mentioned)
2. Constraints: infer from the message and scenario context. Use only these exact keys: "time", "cost", "security", "perf", "downtime", "partial_docs". Examples: deadlines/schedule -> time; budget/expensive -> cost; compliance/audit -> security; latency/throughput -> perf; availability/zero downtime -> downtime; missing docs -> partial_docs. Return a non-empty list when the user discusses or implies any of these.
3. Confidence level (optional: "high", "medium", "low", or null)

Return ONLY a JSON object with this structure (use the key "constraints" in lowercase):
{{
    "strategy": "adapter_layer" | "abstraction" | "hybrid" | "rewrite" | null,
    "constraints": ["time", "cost", ...],
    "confidence": "high" | "medium" | "low" | null
}}

JSON:"""
        
        if self.llm_config.provider == "openai":
            response = client.chat.completions.create(
                model=self.llm_config.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured information from text. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.llm_config.temperature,
                max_tokens=self.llm_config.max_tokens
            )
            content = response.choices[0].message.content.strip()
        else:  # anthropic
            response = client.messages.create(
                model=self.llm_config.model,
                max_tokens=self.llm_config.max_tokens,
                temperature=self.llm_config.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.content[0].text.strip()
        
        # Extract JSON from response
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        try:
            result = json.loads(content)
            # Accept "constraints" or "Constraints" (some LLMs vary)
            raw_constraints = result.get("constraints") or result.get("Constraints") or []
            constraints = _normalize_constraints(raw_constraints)
            return {
                "strategy": result.get("strategy"),
                "constraints": constraints,
                "confidence": result.get("confidence")
            }
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON: {e}") from e
