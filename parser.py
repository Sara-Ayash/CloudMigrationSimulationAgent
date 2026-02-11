"""User response parsing using LLM API."""

import json
from typing import Dict, List, Optional, Any

from config import LLMConfig


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
        """Parse user message to extract strategy, constraints, and confidence."""
        # Try LLM-based parsing first
        try:
            return self._parse_with_llm(user_message)
        except Exception as e:
            # Check for specific error types
            error_msg = str(e)
            print(f"Error: {error_msg}")
            if "quota" in error_msg.lower() or "429" in error_msg or "insufficient_quota" in error_msg:
                # Don't spam warnings for quota errors - only show once
                if not hasattr(self, '_quota_warning_shown'):
                    print("\n⚠️  Note: LLM API quota exceeded. Using rule-based parsing (may be less accurate).")
                    print("   To use LLM features, please check your API key and billing.\n")
                    self._quota_warning_shown = True
            else:
                # Other errors - show warning
                print(f"\n⚠️  Warning: LLM parsing failed ({type(e).__name__}), using rule-based fallback\n")
            # Fallback to rule-based parsing
            return self._parse_rule_based(user_message)
    
    def _parse_with_llm(self, user_message: str) -> Dict[str, Any]:
        """Parse using LLM API."""
        client = self._get_client()
        
        prompt = f"""Analyze the following user message about cloud migration and extract structured information.

User message: "{user_message}"

Extract:
1. Strategy mentioned (one of: "adapter_layer", "abstraction", "hybrid", "rewrite", or null if none mentioned)
2. Constraints mentioned (list of: "time", "cost", "security", "perf", "downtime", "partial_docs")
3. Confidence level (optional: "high", "medium", "low", or null)

Return ONLY a JSON object with this structure:
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
            return {
                "strategy": result.get("strategy"),
                "constraints": result.get("constraints", []),
                "confidence": result.get("confidence")
            }
        except json.JSONDecodeError:
            # If JSON parsing fails, fall back to rule-based
            return self._parse_rule_based(user_message)
    
    def _parse_rule_based(self, user_message: str) -> Dict[str, Any]:
        """Fallback rule-based parsing."""
        message_lower = user_message.lower()
        
        # Detect strategy
        strategy = None
        if any(word in message_lower for word in ["adapter", "adaptation layer", "wrapper"]):
            strategy = "adapter_layer"
        elif any(word in message_lower for word in ["abstraction", "abstract", "interface"]):
            strategy = "abstraction"
        elif any(word in message_lower for word in ["hybrid", "mixed", "combination"]):
            strategy = "hybrid"
        elif any(word in message_lower for word in ["rewrite", "refactor", "reimplement", "from scratch"]):
            strategy = "rewrite"
        
        # Detect constraints
        constraints = []
        constraint_keywords = {
            "time": ["time", "deadline", "urgent", "quick", "fast", "schedule", "timeline"],
            "cost": ["cost", "budget", "price", "expensive", "cheap", "affordable", "money"],
            "security": ["security", "secure", "compliance", "audit", "encryption", "access control"],
            "perf": ["performance", "perf", "speed", "latency", "throughput", "load", "traffic"],
            "downtime": ["downtime", "availability", "zero downtime", "always on", "uptime"],
            "partial_docs": ["documentation", "docs", "documented", "missing docs", "incomplete"]
        }
        
        for constraint, keywords in constraint_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                constraints.append(constraint)
        
        # Detect confidence (simple heuristic)
        confidence = None
        if any(word in message_lower for word in ["definitely", "sure", "certain", "confident"]):
            confidence = "high"
        elif any(word in message_lower for word in ["maybe", "perhaps", "might", "uncertain"]):
            confidence = "low"
        else:
            confidence = "medium"
        
        return {
            "strategy": strategy,
            "constraints": constraints,
            "confidence": confidence
        }


def detect_strategy(user_message: str, parser: UserResponseParser) -> Optional[str]:
    """Detect strategy from user message."""
    extracted = parser.parse_user_response(user_message)
    return extracted.get("strategy")


def detect_constraints(user_message: str, parser: UserResponseParser) -> List[str]:
    """Detect constraints from user message."""
    extracted = parser.parse_user_response(user_message)
    return extracted.get("constraints", [])


def detect_confidence(user_message: str, parser: UserResponseParser) -> Optional[str]:
    """Detect confidence level from user message."""
    extracted = parser.parse_user_response(user_message)
    return extracted.get("confidence")
